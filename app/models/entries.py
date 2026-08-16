from datetime import datetime, timezone

from bson import ObjectId


def day_key(d) -> datetime:
    return datetime(d.year, d.month, d.day)


def month_key(d) -> datetime:
    return datetime(d.year, d.month, 1)


def upsert_entry(db, metric_id, date, value, note=""):
    db.entries.update_one(
        {"metric_id": ObjectId(metric_id), "date": date},
        {
            "$set": {"value": value, "note": note},
            "$setOnInsert": {"created_at": datetime.now(timezone.utc)},
        },
        upsert=True,
    )


def get_entry(db, metric_id, date):
    return db.entries.find_one({"metric_id": ObjectId(metric_id), "date": date})


def entries_for_metrics_on(db, metric_ids, date):
    docs = db.entries.find({"metric_id": {"$in": [ObjectId(m) for m in metric_ids]}, "date": date})
    return {str(d["metric_id"]): d for d in docs}


def entries_for_metric(db, metric_id, start=None, end=None):
    query = {"metric_id": ObjectId(metric_id)}
    if start or end:
        query["date"] = {}
        if start:
            query["date"]["$gte"] = start
        if end:
            query["date"]["$lte"] = end
    return list(db.entries.find(query).sort("date", 1))


def latest_entry(db, metric_id):
    docs = list(db.entries.find({"metric_id": ObjectId(metric_id)}).sort("date", -1).limit(1))
    return docs[0] if docs else None
