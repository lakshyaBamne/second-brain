"""One-time migration: enables transaction tracking on the Finances aspect
and archives the old Expenditures/Savings/Investments/Current debt metrics.
Their historical entries are preserved (archiving, not deleting) - those
figures now come from the transaction log instead of manual entry. Safe to
run more than once."""

import os

from dotenv import load_dotenv

load_dotenv()

from app.db import get_db  # noqa: E402
from app.models.life_aspects import get_aspect_by_slug, update_aspect  # noqa: E402
from app.models.metrics import archive_metric, list_metrics  # noqa: E402

ARCHIVE_NAMES = {"Expenditures", "Savings", "Investments", "Current debt"}


def main():
    uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
    dbname = os.environ.get("MONGO_DBNAME", "second_brain")
    db = get_db(uri, dbname)

    aspect = get_aspect_by_slug(db, "finances")
    if not aspect:
        print("No Finances aspect found - nothing to migrate.")
        return

    if not aspect.get("tracks_transactions"):
        update_aspect(db, aspect["_id"], {"tracks_transactions": True})
        print("Enabled transaction tracking on Finances.")
    else:
        print("Finances already tracks transactions - skipping.")

    for metric in list_metrics(db, aspect_id=aspect["_id"], active_only=True):
        if metric["name"] in ARCHIVE_NAMES:
            archive_metric(db, metric["_id"])
            print(f"Archived metric: {metric['name']} (historical entries kept)")

    print("Migration complete.")


if __name__ == "__main__":
    main()
