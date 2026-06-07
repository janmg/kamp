"""Change log view routes."""

from __future__ import annotations

from flask import Blueprint, render_template

from web.services.admin_service import list_logs
from models import get_session
from web.auth import login_required

log_bp = Blueprint("log", __name__)


@log_bp.route("/log")
@login_required
def log_view():
    session = get_session()
    try:
        rows = list_logs(session)
    finally:
        session.close()
    return render_template("log.html", rows=rows)
