"""Authentication routes."""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from config import PASSCODE, ADMIN_PASSCODE

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Login page to authenticate with passcode."""
    if request.method == "POST":
        passcode = request.form.get("passcode", "").strip()
        
        if ADMIN_PASSCODE and passcode == ADMIN_PASSCODE:
            # Admin login
            session["authenticated"] = True
            session["is_admin"] = True
            session.permanent = True
            next_page = request.args.get("next")
            if next_page and next_page.startswith("/"):
                return redirect(next_page)
            return redirect(url_for("dashboard.index"))
        elif passcode == PASSCODE:
            # Regular user login
            session["authenticated"] = True
            session["is_admin"] = False
            session.permanent = True
            next_page = request.args.get("next")
            if next_page and next_page.startswith("/"):
                return redirect(next_page)
            return redirect(url_for("dashboard.index"))
        else:
            flash("Incorrect passcode. Please try again.", "error")
    
    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    """Logout and clear session."""
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
