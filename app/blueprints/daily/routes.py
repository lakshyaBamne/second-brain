from datetime import date, datetime, timedelta

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.models import entries as entries_model
from app.models import life_aspects
from app.models import metrics as metrics_model
from app.models import transactions as transactions_model

daily_bp = Blueprint("daily", __name__, url_prefix="/today")


def _parse_date(s):
    if not s:
        return date.today()
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return date.today()


@daily_bp.route("", methods=["GET"])
@login_required
def today():
    db = current_app.db
    the_date = _parse_date(request.args.get("date"))
    day = entries_model.day_key(the_date)

    groups = []
    for aspect in life_aspects.list_aspects(db):
        daily_metrics = metrics_model.list_metrics(db, aspect_id=aspect["_id"], cadence="daily")
        rows = []
        if daily_metrics:
            existing = entries_model.entries_for_metrics_on(db, [m["_id"] for m in daily_metrics], day)
            rows = [{"metric": m, "value": existing.get(str(m["_id"]), {}).get("value")} for m in daily_metrics]

        transaction_config = aspect.get("transaction_config")
        if not rows and not transaction_config:
            continue

        groups.append(
            {
                "aspect": aspect,
                "rows": rows,
                "transaction_config": transaction_config,
                "transactions": transactions_model.transactions_for_day(db, aspect["_id"], day)
                if transaction_config
                else [],
            }
        )

    logged = sum(1 for g in groups for r in g["rows"] if r["value"] is not None)
    total = sum(len(g["rows"]) for g in groups)

    return render_template(
        "daily/today.html",
        groups=groups,
        the_date=the_date,
        prev_date=the_date - timedelta(days=1),
        next_date=the_date + timedelta(days=1),
        today=date.today(),
        logged=logged,
        total=total,
    )


@daily_bp.route("", methods=["POST"])
@login_required
def save_today():
    db = current_app.db
    the_date = _parse_date(request.form.get("date"))
    day = entries_model.day_key(the_date)

    for aspect in life_aspects.list_aspects(db):
        for metric in metrics_model.list_metrics(db, aspect_id=aspect["_id"], cadence="daily"):
            field = f"metric_{metric['_id']}"
            if metric["type"] == "boolean":
                value = field in request.form
            else:
                raw = request.form.get(field)
                if raw in (None, ""):
                    continue
                value = int(raw) if metric["type"] == "rating" else float(raw)
            entries_model.upsert_entry(db, metric["_id"], day, value)

        transaction_config = aspect.get("transaction_config")
        if transaction_config:
            valid_categories = set(transaction_config.get("categories", []))
            count = int(request.form.get(f"txn_count_{aspect['_id']}", 0) or 0)
            for i in range(count):
                prefix = f"txn_{aspect['_id']}_{i}_"
                name = request.form.get(prefix + "name", "").strip()
                amount_raw = request.form.get(prefix + "amount", "")
                category = request.form.get(prefix + "category", "")
                if not name or not amount_raw or category not in valid_categories:
                    continue
                description = request.form.get(prefix + "description", "").strip()
                transactions_model.add_transaction(db, aspect["_id"], day, name, description, float(amount_raw), category)

    flash("Saved today's entries.", "success")
    return redirect(url_for("daily.today", date=the_date.isoformat()))


@daily_bp.route("/transactions/<transaction_id>/delete", methods=["POST"])
@login_required
def delete_transaction(transaction_id):
    transactions_model.delete_transaction(current_app.db, transaction_id)
    redirect_date = request.form.get("date", date.today().isoformat())
    return redirect(url_for("daily.today", date=redirect_date))
