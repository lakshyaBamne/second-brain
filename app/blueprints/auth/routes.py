from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user

from app.models.users import get_user_by_email

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "")
        password = request.form.get("password", "")
        user = get_user_by_email(current_app.db, email)
        if user and user.check_password(password):
            login_user(user, remember=True)
            next_url = request.args.get("next") or url_for("dashboard.home")
            return redirect(next_url)
        flash("Incorrect email or password.", "error")
    return render_template("auth/login.html")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
