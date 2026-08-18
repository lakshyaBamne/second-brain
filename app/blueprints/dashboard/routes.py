from datetime import date, timedelta

from flask import Blueprint, abort, current_app, render_template, request
from flask_login import login_required

from app import analytics
from app.models import entries as entries_model
from app.models import life_aspects
from app.models import metrics as metrics_model
from app.models import transactions as transactions_model

dashboard_bp = Blueprint("dashboard", __name__)

RANGE_DAYS = {"week": 7, "month": 30, "quarter": 90, "all": None}


def _transaction_daily_totals(db, aspect_id, days=30):
    end = entries_model.day_key(date.today())
    start = end - timedelta(days=days)
    docs = transactions_model.transactions_for_range(db, aspect_id, start=start, end=end)
    totals = {}
    for doc in docs:
        key = doc["date"].strftime("%Y-%m-%d")
        totals[key] = totals.get(key, 0.0) + doc["amount"]
    return [{"date": d, "value": v} for d, v in sorted(totals.items())]


@dashboard_bp.route("/")
@login_required
def home():
    db = current_app.db
    cards = []
    for aspect in life_aspects.list_aspects(db):
        aspect_metrics = [
            m for m in metrics_model.list_metrics(db, aspect_id=aspect["_id"]) if m["cadence"] != "weekly"
        ]
        headline = aspect_metrics[0] if aspect_metrics else None
        card = {"aspect": aspect, "headline": headline, "series": [], "status": None, "latest": None, "transaction_total": None}
        if headline:
            card["series"] = analytics.sparkline_series(db, headline, days=30)
            card["status"] = analytics.status_for_metric(db, headline)
            latest = entries_model.latest_entry(db, headline["_id"])
            card["latest"] = latest["value"] if latest else None
        elif aspect.get("transaction_config"):
            card["series"] = _transaction_daily_totals(db, aspect["_id"], days=30)
            card["transaction_total"] = sum(point["value"] for point in card["series"])
        cards.append(card)
    return render_template("dashboard/home.html", cards=cards)


@dashboard_bp.route("/aspects/<slug>")
@login_required
def aspect_detail(slug):
    db = current_app.db
    aspect = life_aspects.get_aspect_by_slug(db, slug)
    if not aspect:
        abort(404)

    range_key = request.args.get("range", "month")
    days = RANGE_DAYS.get(range_key, 30)
    start = entries_model.day_key(date.today() - timedelta(days=days)) if days is not None else None

    metric_charts = []
    for metric in metrics_model.list_metrics(db, aspect_id=aspect["_id"]):
        if metric["cadence"] == "weekly":
            continue
        docs = entries_model.entries_for_metric(db, metric["_id"], start=start)
        metric_charts.append(
            {
                "metric": metric,
                "series": [{"date": d["date"].strftime("%Y-%m-%d"), "value": d["value"]} for d in docs],
                "status": analytics.status_for_metric(db, metric),
            }
        )

    transaction_summary = None
    transaction_config = aspect.get("transaction_config")
    if transaction_config:
        categories = transaction_config.get("categories", [])
        totals = transactions_model.totals_by_category(db, aspect["_id"], categories, start)
        transaction_summary = {
            "amount_label": transaction_config.get("amount_label", "Amount"),
            "labels": categories,
            "amounts": [totals[c] for c in categories],
            "totals": [(c, totals[c]) for c in categories],
        }

    return render_template(
        "dashboard/aspect_detail.html",
        aspect=aspect,
        metric_charts=metric_charts,
        transaction_summary=transaction_summary,
        range_key=range_key,
    )
