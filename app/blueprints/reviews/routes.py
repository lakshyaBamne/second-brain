from datetime import date, datetime

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.models import entries as entries_model
from app.models import life_aspects
from app.models import metrics as metrics_model
from app.models import reviews as reviews_model

reviews_bp = Blueprint("reviews", __name__, url_prefix="/reviews")

PROMPTS = [
    ("highlights", "What went well this month?"),
    ("lowlights", "What needs improvement?"),
    ("focus_next", "What's your focus for next month?"),
]


def _month_bounds(period_start: datetime):
    if period_start.month == 12:
        next_month = datetime(period_start.year + 1, 1, 1)
    else:
        next_month = datetime(period_start.year, period_start.month + 1, 1)
    return period_start, next_month


def _prev_month_start(period_start: datetime):
    if period_start.month == 1:
        return datetime(period_start.year - 1, 12, 1)
    return datetime(period_start.year, period_start.month - 1, 1)


def _avg(docs):
    values = [d["value"] for d in docs if isinstance(d["value"], (int, float))]
    return sum(values) / len(values) if values else None


@reviews_bp.route("/")
@login_required
def history():
    db = current_app.db
    return render_template(
        "reviews/history.html",
        reviews=reviews_model.list_reviews(db),
        current_month=entries_model.month_key(date.today()),
    )


@reviews_bp.route("/<period>", methods=["GET", "POST"])
@login_required
def review(period):
    db = current_app.db
    try:
        year_str, month_str = period.split("-")
        period_start = datetime(int(year_str), int(month_str), 1)
    except (ValueError, TypeError):
        abort(404)

    aspects = life_aspects.list_aspects(db)

    if request.method == "POST":
        reflections = []
        for aspect in aspects:
            reflections.append(
                {
                    "aspect_id": aspect["_id"],
                    "highlights": request.form.get(f"highlights_{aspect['_id']}", "").strip(),
                    "lowlights": request.form.get(f"lowlights_{aspect['_id']}", "").strip(),
                    "focus_next": request.form.get(f"focus_next_{aspect['_id']}", "").strip(),
                }
            )
            for metric in metrics_model.list_metrics(db, aspect_id=aspect["_id"], cadence="monthly"):
                raw = request.form.get(f"metric_{metric['_id']}")
                if raw not in (None, ""):
                    entries_model.upsert_entry(db, metric["_id"], period_start, float(raw))
        reviews_model.upsert_review(db, period_start, reflections)
        flash(f"Saved your {period_start.strftime('%B %Y')} review.", "success")
        return redirect(url_for("reviews.review", period=period))

    existing = reviews_model.get_review(db, period_start)
    existing_by_aspect = {}
    if existing:
        existing_by_aspect = {str(r["aspect_id"]): r for r in existing.get("aspect_reflections", [])}

    month_start, month_end = _month_bounds(period_start)
    prev_start = _prev_month_start(period_start)

    aspect_sections = []
    for aspect in aspects:
        metric_summaries = []
        monthly_inputs = []
        for metric in metrics_model.list_metrics(db, aspect_id=aspect["_id"]):
            this_month = entries_model.entries_for_metric(db, metric["_id"], start=month_start, end=month_end)
            last_month = entries_model.entries_for_metric(db, metric["_id"], start=prev_start, end=month_start)
            metric_summaries.append(
                {
                    "metric": metric,
                    "this_month_avg": _avg(this_month),
                    "last_month_avg": _avg(last_month),
                }
            )
            if metric["cadence"] == "monthly":
                monthly_inputs.append({"metric": metric, "value": this_month[0]["value"] if this_month else None})
        aspect_sections.append(
            {
                "aspect": aspect,
                "metrics": metric_summaries,
                "monthly_inputs": monthly_inputs,
                "existing": existing_by_aspect.get(str(aspect["_id"]), {}),
            }
        )

    return render_template(
        "reviews/review_form.html",
        period=period,
        period_start=period_start,
        aspect_sections=aspect_sections,
        prompts=PROMPTS,
    )
