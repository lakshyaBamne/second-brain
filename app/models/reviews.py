from datetime import datetime, timezone


def get_review(db, period_start: datetime):
    return db.reviews.find_one({"period_type": "monthly", "period_start": period_start})


def upsert_review(db, period_start: datetime, aspect_reflections: list):
    db.reviews.update_one(
        {"period_type": "monthly", "period_start": period_start},
        {
            "$set": {"aspect_reflections": aspect_reflections},
            "$currentDate": {"completed_at": True},
            "$setOnInsert": {"period_type": "monthly", "period_start": period_start},
        },
        upsert=True,
    )


def list_reviews(db):
    return list(db.reviews.find({"period_type": "monthly"}).sort("period_start", -1))
