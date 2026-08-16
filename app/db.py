from pymongo import MongoClient


def get_db(uri: str, db_name: str):
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    return client[db_name]


def ensure_indexes(db):
    db.entries.create_index([("metric_id", 1), ("date", 1)], unique=True)
    db.reviews.create_index([("period_type", 1), ("period_start", 1)], unique=True)
    db.users.create_index("email", unique=True)
    db.life_aspects.create_index("slug", unique=True)
