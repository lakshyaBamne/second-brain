from datetime import datetime, timezone

from bson import ObjectId


def add_transaction(db, aspect_id, date, name, description, amount, category):
    doc = {
        "aspect_id": ObjectId(aspect_id),
        "date": date,
        "name": name,
        "description": description,
        "amount": amount,
        "category": category,
        "created_at": datetime.now(timezone.utc),
    }
    result = db.transactions.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


def transactions_for_day(db, aspect_id, date):
    return list(db.transactions.find({"aspect_id": ObjectId(aspect_id), "date": date}).sort("created_at", 1))


def transactions_for_range(db, aspect_id, start=None, end=None):
    query = {"aspect_id": ObjectId(aspect_id)}
    if start or end:
        query["date"] = {}
        if start:
            query["date"]["$gte"] = start
        if end:
            query["date"]["$lte"] = end
    return list(db.transactions.find(query).sort("date", 1))


def totals_by_category(db, aspect_id, categories, start=None, end=None):
    totals = {c: 0.0 for c in categories}
    for doc in transactions_for_range(db, aspect_id, start, end):
        totals[doc["category"]] = totals.get(doc["category"], 0.0) + doc["amount"]
    return totals


def delete_transaction(db, transaction_id):
    db.transactions.delete_one({"_id": ObjectId(transaction_id)})
