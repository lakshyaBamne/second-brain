"""One-time migration: converts the old boolean `tracks_transactions` flag
into the new configurable `transaction_config` (custom categories + a custom
amount label per aspect, e.g. Finances gets Expenditure/Savings/Investments/
Debt in currency, a Health aspect could get Gym/Sports/Others in hours).
Safe to run more than once."""

import os

from dotenv import load_dotenv

load_dotenv()

from app.db import get_db  # noqa: E402

DEFAULT_FINANCE_CONFIG = {
    "amount_label": "Amount",
    "categories": ["Expenditure", "Savings", "Investments", "Debt"],
}


def main():
    uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
    dbname = os.environ.get("MONGO_DBNAME", "second_brain")
    db = get_db(uri, dbname)

    updated = 0
    for aspect in db.life_aspects.find({"tracks_transactions": True, "transaction_config": {"$exists": False}}):
        db.life_aspects.update_one(
            {"_id": aspect["_id"]},
            {"$set": {"transaction_config": DEFAULT_FINANCE_CONFIG}, "$unset": {"tracks_transactions": ""}},
        )
        print(f"Migrated '{aspect['name']}' to a configurable quick-add log (Expenditure/Savings/Investments/Debt).")
        updated += 1

    # clear the stale flag off any aspect that never had it enabled
    result = db.life_aspects.update_many({"tracks_transactions": False}, {"$unset": {"tracks_transactions": ""}})
    if result.modified_count:
        print(f"Cleared stale flag on {result.modified_count} other aspect(s).")

    if updated == 0:
        print("Nothing to migrate.")

    # existing transactions were saved with the old lowercase category keys
    # (e.g. "expenditure") - re-case them to match each aspect's configured
    # category names exactly, or they'd silently drop out of review totals
    recased = 0
    for aspect in db.life_aspects.find({"transaction_config": {"$ne": None}}):
        categories = aspect.get("transaction_config", {}).get("categories", [])
        by_lower = {c.lower(): c for c in categories}
        for txn in db.transactions.find({"aspect_id": aspect["_id"]}):
            canonical = by_lower.get(txn["category"].lower())
            if canonical and canonical != txn["category"]:
                db.transactions.update_one({"_id": txn["_id"]}, {"$set": {"category": canonical}})
                recased += 1
    if recased:
        print(f"Re-cased {recased} existing transaction(s) to match current category names.")

    print("Migration complete.")


if __name__ == "__main__":
    main()
