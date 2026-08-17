"""One-time setup: creates your login and seeds the Finances life aspect
(transaction-tracking enabled) with its one manual monthly metric, In-hand
money. Expenditure/Savings/Investments/Current debt are tracked via the
transaction log on the Today page instead."""

import os
from getpass import getpass

from dotenv import load_dotenv

load_dotenv()

from app.db import ensure_indexes, get_db  # noqa: E402
from app.models.life_aspects import create_aspect, get_aspect_by_slug  # noqa: E402
from app.models.metrics import create_metric, list_metrics  # noqa: E402
from app.models.users import any_user_exists, create_user  # noqa: E402

SEED_METRICS = [
    ("In-hand money", "number", "monthly", "currency", None),
]


def main():
    uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
    dbname = os.environ.get("MONGO_DBNAME", "second_brain")
    db = get_db(uri, dbname)
    ensure_indexes(db)

    if any_user_exists(db):
        print("A user already exists — skipping login creation.")
    else:
        print("No user found — let's create your login.")
        email = input("Email: ").strip()
        password = getpass("Password: ")
        create_user(db, email, password)
        print(f"Created user {email}.")

    aspect = get_aspect_by_slug(db, "finances")
    if aspect:
        print("Finances aspect already exists — skipping.")
    else:
        finances_config = {
            "amount_label": "Amount",
            "categories": ["Expenditure", "Savings", "Investments", "Debt"],
        }
        aspect = create_aspect(db, "Finances", transaction_config=finances_config)
        print("Created life aspect: Finances (quick-add log enabled)")

    existing_names = {m["name"] for m in list_metrics(db, aspect_id=aspect["_id"], active_only=False)}
    for name, type_, cadence, unit, target in SEED_METRICS:
        if name in existing_names:
            continue
        create_metric(db, aspect["_id"], name, type_, cadence, unit, target)
        print(f"Created metric: {name} ({cadence})")

    print("Seed complete. Run `python wsgi.py` and log in.")


if __name__ == "__main__":
    main()
