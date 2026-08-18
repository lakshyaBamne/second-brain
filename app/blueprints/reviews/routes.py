import calendar
from datetime import date, datetime

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.models import entries as entries_model
from app.models import life_aspects
from app.models import metrics as metrics_model
from app.models import reviews as reviews_model
from app.models import transactions as transactions_model

reviews_bp = Blueprint("reviews", __name__, url_prefix="/reviews")

PROMPTS = [
    ("highlights", "What went well this month?"),
    ("lowlights", "What needs improvement?"),
    ("focus_next", "What's your focus for next month?"),
]

WEEKLY_PROMPTS = [
    ("highlights", "What went well this week?"),
    ("lowlights", "What needs improvement?"),
    ("focus_next", "What's your focus for next week?"),
]

WEEKS_PER_MONTH = 4


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


def _week_bounds(month_start: datetime, week_num: int):
    """Each month is split into 4 fixed buckets: days 1-7, 8-14, 15-21, 22-end."""
    days_in_month = calendar.monthrange(month_start.year, month_start.month)[1]
    if week_num < WEEKS_PER_MONTH:
        start_day = (week_num - 1) * 7 + 1
        end_day = start_day + 6
    else:
        start_day = 22
        end_day = days_in_month
    start = datetime(month_start.year, month_start.month, start_day)
    end = datetime(month_start.year, month_start.month, end_day)
    return start, end


def _week_num_for_day(day: int) -> int:
    if day <= 7:
        return 1
    if day <= 14:
        return 2
    if day <= 21:
        return 3
    return WEEKS_PER_MONTH


def _avg(docs):
    values = [d["value"] for d in docs if isinstance(d["value"], (int, float))]
    return sum(values) / len(values) if values else None


@reviews_bp.route("/")
@login_required
def history():
    db = current_app.db
    today = date.today()
    current_month = entries_model.month_key(today)
    current_week_num = _week_num_for_day(today.day)

    monthly_docs = {r["period_start"] for r in reviews_model.list_reviews(db, "monthly")}
    weekly_docs = {r["period_start"] for r in reviews_model.list_reviews(db, "weekly")}

    month_starts = {d.replace(day=1) for d in monthly_docs} | {d.replace(day=1) for d in weekly_docs} | {current_month}
    ordered_months = sorted(month_starts, reverse=True)

    cards = []
    for month_start in ordered_months:
        is_current = month_start == current_month
        weeks = []
        for week_num in range(1, WEEKS_PER_MONTH + 1):
            w_start, w_end = _week_bounds(month_start, week_num)
            weeks.append(
                {
                    "num": week_num,
                    "start": w_start,
                    "end": w_end,
                    "is_current": is_current and week_num == current_week_num,
                    "completed": w_start in weekly_docs,
                }
            )
        cards.append(
            {
                "month_start": month_start,
                "is_current": is_current,
                "weeks": weeks,
                "month_completed": month_start in monthly_docs,
            }
        )

    current_card = cards[0] if cards and cards[0]["is_current"] else None
    other_cards = cards[1:] if current_card else cards

    return render_template("reviews/history.html", current_card=current_card, other_cards=other_cards)


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
        reviews_model.upsert_review(db, "monthly", period_start, reflections)
        flash(f"Saved your {period_start.strftime('%B %Y')} review.", "success")
        return redirect(url_for("reviews.review", period=period))

    existing = reviews_model.get_review(db, "monthly", period_start)
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
            if metric["cadence"] == "weekly":
                continue
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

        transaction_summary = None
        transaction_config = aspect.get("transaction_config")
        if transaction_config:
            categories = transaction_config.get("categories", [])
            this_totals = transactions_model.totals_by_category(db, aspect["_id"], categories, month_start, month_end)
            last_totals = transactions_model.totals_by_category(db, aspect["_id"], categories, prev_start, month_start)
            transaction_summary = {
                "amount_label": transaction_config.get("amount_label", "Amount"),
                "labels": categories,
                "this_month": [this_totals[c] for c in categories],
                "last_month": [last_totals[c] for c in categories],
                "totals": [(c, this_totals[c]) for c in categories],
            }

        aspect_sections.append(
            {
                "aspect": aspect,
                "metrics": metric_summaries,
                "monthly_inputs": monthly_inputs,
                "transaction_summary": transaction_summary,
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


@reviews_bp.route("/<period>/week/<int:week_num>", methods=["GET", "POST"])
@login_required
def weekly_review(period, week_num):
    db = current_app.db
    if week_num < 1 or week_num > WEEKS_PER_MONTH:
        abort(404)
    try:
        year_str, month_str = period.split("-")
        month_start = datetime(int(year_str), int(month_str), 1)
    except (ValueError, TypeError):
        abort(404)

    week_start, week_end = _week_bounds(month_start, week_num)
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
            for metric in metrics_model.list_metrics(db, aspect_id=aspect["_id"], cadence="weekly"):
                raw = request.form.get(f"metric_{metric['_id']}")
                if raw not in (None, ""):
                    entries_model.upsert_entry(db, metric["_id"], week_start, float(raw))
        reviews_model.upsert_review(db, "weekly", week_start, reflections)
        flash(f"Saved your Week {week_num} review.", "success")
        return redirect(url_for("reviews.weekly_review", period=period, week_num=week_num))

    existing = reviews_model.get_review(db, "weekly", week_start)
    existing_by_aspect = {}
    if existing:
        existing_by_aspect = {str(r["aspect_id"]): r for r in existing.get("aspect_reflections", [])}

    aspect_sections = []
    for aspect in aspects:
        weekly_inputs = []
        for metric in metrics_model.list_metrics(db, aspect_id=aspect["_id"], cadence="weekly"):
            entry = entries_model.get_entry(db, metric["_id"], week_start)
            weekly_inputs.append({"metric": metric, "value": entry["value"] if entry else None})
        aspect_sections.append(
            {
                "aspect": aspect,
                "weekly_inputs": weekly_inputs,
                "existing": existing_by_aspect.get(str(aspect["_id"]), {}),
            }
        )

    return render_template(
        "reviews/weekly_review_form.html",
        period=period,
        week_num=week_num,
        month_start=month_start,
        week_start=week_start,
        week_end=week_end,
        aspect_sections=aspect_sections,
        prompts=WEEKLY_PROMPTS,
    )
