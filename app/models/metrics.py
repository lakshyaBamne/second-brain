from bson import ObjectId

METRIC_TYPES = ("number", "boolean", "rating")
CADENCES = ("daily", "weekly", "monthly")


def list_metrics(db, aspect_id=None, cadence=None, active_only=True):
    query = {}
    if aspect_id:
        query["aspect_id"] = ObjectId(aspect_id)
    if cadence:
        query["cadence"] = cadence
    if active_only:
        query["active"] = True
    return list(db.metrics.find(query).sort("order", 1))


def get_metric(db, metric_id):
    return db.metrics.find_one({"_id": ObjectId(metric_id)})


def create_metric(db, aspect_id, name, type_, cadence, unit="", target=None):
    assert type_ in METRIC_TYPES
    assert cadence in CADENCES
    order = db.metrics.count_documents({"aspect_id": ObjectId(aspect_id)})
    doc = {
        "aspect_id": ObjectId(aspect_id),
        "name": name,
        "type": type_,
        "cadence": cadence,
        "unit": unit,
        "target": target,
        "active": True,
        "order": order,
    }
    result = db.metrics.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


def update_metric(db, metric_id, updates):
    db.metrics.update_one({"_id": ObjectId(metric_id)}, {"$set": updates})


def archive_metric(db, metric_id):
    db.metrics.update_one({"_id": ObjectId(metric_id)}, {"$set": {"active": False}})


def reactivate_metric(db, metric_id):
    db.metrics.update_one({"_id": ObjectId(metric_id)}, {"$set": {"active": True}})
