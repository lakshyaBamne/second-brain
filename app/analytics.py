from datetime import date, timedelta

from app.models import entries as entries_model


def sparkline_series(db, metric, days=30):
    end = entries_model.day_key(date.today())
    start = end - timedelta(days=days)
    docs = entries_model.entries_for_metric(db, metric["_id"], start=start, end=end)
    return [{"date": d["date"].strftime("%Y-%m-%d"), "value": d["value"]} for d in docs]


def status_for_metric(db, metric):
    """'good' | 'warning' | None, based on the latest value vs. the metric's target."""
    target = metric.get("target")
    if not target:
        return None
    latest = entries_model.latest_entry(db, metric["_id"])
    if latest is None or not isinstance(latest["value"], (int, float)):
        return None
    value = latest["value"]
    goal = target["value"]
    on_track = value >= goal if target["direction"] == "at_least" else value <= goal
    return "good" if on_track else "warning"
