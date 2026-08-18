from datetime import datetime, timezone

PERIOD_TYPES = ("weekly", "monthly")


def get_review(db, period_type: str, period_start: datetime):
    return db.reviews.find_one({"period_type": period_type, "period_start": period_start})


def upsert_review(db, period_type: str, period_start: datetime, aspect_reflections: list):
    db.reviews.update_one(
        {"period_type": period_type, "period_start": period_start},
        {
            "$set": {"aspect_reflections": aspect_reflections},
            "$currentDate": {"completed_at": True},
            "$setOnInsert": {"period_type": period_type, "period_start": period_start},
        },
        upsert=True,
    )


def list_reviews(db, period_type: str):
    return list(db.reviews.find({"period_type": period_type}).sort("period_start", -1))
