from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.models import life_aspects
from app.models import metrics as metrics_model

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


def _parse_transaction_config(form):
    """Build a transaction_config dict from the shared add/edit form fields,
    or None if the log isn't enabled / no valid categories were given."""
    if "enable_transactions" not in form:
        return None
    seen = set()
    categories = []
    for raw in form.get("categories", "").split(","):
        name = raw.strip()
        if name and name not in seen:
            seen.add(name)
            categories.append(name)
    if not categories:
        return None
    amount_label = form.get("amount_label", "").strip() or "Amount"
    return {"amount_label": amount_label, "categories": categories}


@settings_bp.route("/aspects", methods=["GET", "POST"])
@login_required
def aspects():
    db = current_app.db
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        transaction_config = _parse_transaction_config(request.form)
        if name:
            life_aspects.create_aspect(db, name, transaction_config=transaction_config)
            flash(f'Added life aspect "{name}".', "success")
        return redirect(url_for("settings.aspects"))
    return render_template("settings/aspects.html", aspects=life_aspects.list_aspects(db))


@settings_bp.route("/aspects/<aspect_id>/transaction_config", methods=["POST"])
@login_required
def update_transaction_config(aspect_id):
    transaction_config = _parse_transaction_config(request.form)
    life_aspects.update_transaction_config(current_app.db, aspect_id, transaction_config)
    flash("Updated quick-add log settings.", "success")
    return redirect(url_for("settings.aspects"))


@settings_bp.route("/aspects/<aspect_id>/rename", methods=["POST"])
@login_required
def rename_aspect(aspect_id):
    name = request.form.get("name", "").strip()
    if name:
        life_aspects.update_aspect(current_app.db, aspect_id, {"name": name})
    return redirect(url_for("settings.aspects"))


@settings_bp.route("/aspects/<aspect_id>/delete", methods=["POST"])
@login_required
def delete_aspect(aspect_id):
    life_aspects.delete_aspect(current_app.db, aspect_id)
    flash("Life aspect deleted, along with its metrics and entries.", "success")
    return redirect(url_for("settings.aspects"))


@settings_bp.route("/metrics", methods=["GET", "POST"])
@login_required
def metrics():
    db = current_app.db
    all_aspects = life_aspects.list_aspects(db)

    if request.method == "POST":
        aspect_id = request.form.get("aspect_id")
        name = request.form.get("name", "").strip()
        type_ = request.form.get("type")
        cadence = request.form.get("cadence")
        unit = request.form.get("unit", "").strip()

        target = None
        target_value = request.form.get("target_value")
        target_direction = request.form.get("target_direction")
        if target_value and target_direction:
            target = {"value": float(target_value), "direction": target_direction}

        if aspect_id and name and type_ in metrics_model.METRIC_TYPES and cadence in metrics_model.CADENCES:
            metrics_model.create_metric(db, aspect_id, name, type_, cadence, unit, target)
            flash(f'Added metric "{name}".', "success")
        return redirect(url_for("settings.metrics"))

    grouped = [
        {"aspect": aspect, "metrics": metrics_model.list_metrics(db, aspect_id=aspect["_id"], active_only=False)}
        for aspect in all_aspects
    ]
    return render_template(
        "settings/metrics.html",
        grouped=grouped,
        aspects=all_aspects,
        types=metrics_model.METRIC_TYPES,
        cadences=metrics_model.CADENCES,
    )


@settings_bp.route("/metrics/<metric_id>/archive", methods=["POST"])
@login_required
def archive_metric(metric_id):
    metrics_model.archive_metric(current_app.db, metric_id)
    return redirect(url_for("settings.metrics"))


@settings_bp.route("/metrics/<metric_id>/reactivate", methods=["POST"])
@login_required
def reactivate_metric(metric_id):
    metrics_model.reactivate_metric(current_app.db, metric_id)
    return redirect(url_for("settings.metrics"))
