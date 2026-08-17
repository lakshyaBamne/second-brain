import re

from bson import ObjectId

from app.colors import slot_for_order


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return slug or "aspect"


def list_aspects(db):
    return list(db.life_aspects.find().sort("order", 1))


def get_aspect(db, aspect_id):
    return db.life_aspects.find_one({"_id": ObjectId(aspect_id)})


def get_aspect_by_slug(db, slug):
    return db.life_aspects.find_one({"slug": slug})


def create_aspect(db, name, icon="", transaction_config=None):
    order = db.life_aspects.count_documents({})
    color = slot_for_order(order)
    slug = _slugify(name)
    base_slug, i = slug, 2
    while db.life_aspects.find_one({"slug": slug}):
        slug = f"{base_slug}-{i}"
        i += 1
    doc = {
        "name": name,
        "slug": slug,
        "color_light": color["light"],
        "color_dark": color["dark"],
        "icon": icon,
        "order": order,
        # None = no quick-add log; otherwise { amount_label, categories: [str, ...] }
        "transaction_config": transaction_config,
    }
    result = db.life_aspects.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


def update_aspect(db, aspect_id, updates):
    db.life_aspects.update_one({"_id": ObjectId(aspect_id)}, {"$set": updates})


def update_transaction_config(db, aspect_id, transaction_config):
    db.life_aspects.update_one({"_id": ObjectId(aspect_id)}, {"$set": {"transaction_config": transaction_config}})


def delete_aspect(db, aspect_id):
    aid = ObjectId(aspect_id)
    metric_ids = [m["_id"] for m in db.metrics.find({"aspect_id": aid}, {"_id": 1})]
    db.entries.delete_many({"metric_id": {"$in": metric_ids}})
    db.metrics.delete_many({"aspect_id": aid})
    db.transactions.delete_many({"aspect_id": aid})
    db.life_aspects.delete_one({"_id": aid})
