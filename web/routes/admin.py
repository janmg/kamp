"""Administrative operation routes (app3 functionality)."""

from __future__ import annotations

from datetime import date, datetime, timezone, timedelta
try:
    from zoneinfo import ZoneInfo
    _EEST = ZoneInfo("Europe/Helsinki")
except Exception:
    _EEST = timezone(timedelta(hours=3))  # UTC+3 fallback (Helsinki summer time)

from flask import Blueprint, Response, flash, redirect, render_template, request, session as flask_session, url_for

from models import Participant, Task, get_session
from web.services import admin_service
from web.services.schedule_service import generate_per_person_csv, generate_points_csv, generate_schedule_csv, run_schedule, run_schedule_stream
from web.auth import login_required

admin_bp = Blueprint("admin", __name__)


def _to_int(value: str | None, field_name: str) -> int:
    if not value:
        raise ValueError(f"{field_name} is required.")
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a number.") from exc


def _future_task_and_day_options(tasks: list[dict]) -> tuple[list[dict], list[int]]:
    now = datetime.now(_EEST)
    event_start = date(2026, 6, 3)  # Wednesday = day 1
    event_end = date(2026, 6, 6)  # Saturday = day 4

    if now.date() < event_start:
        all_days = sorted({int(task["day"]) for task in tasks})
        return tasks, all_days

    if now.date() > event_end:
        return [], []

    current_event_day = (now.date() - event_start).days + 1

    current_time_hhmm = now.strftime("%H:%M")
    future_tasks: list[dict] = []
    for task in tasks:
        day = int(task["day"])
        begin_hhmm = str(task.get("time", "")).split("-", 1)[0]
        if day > current_event_day:
            future_tasks.append(task)
        elif day == current_event_day and begin_hhmm >= current_time_hhmm:
            future_tasks.append(task)

    future_days = sorted({int(task["day"]) for task in future_tasks})
    return future_tasks, future_days


@admin_bp.route("/admin/candidates/<int:task_id>", methods=["GET"])
@login_required
def get_task_candidates(task_id: int):
    """Get available candidates for a task (JSON endpoint)."""
    from flask import jsonify
    session = get_session()
    try:
        candidates = admin_service.get_task_candidates(session, task_id, limit=5)
        return jsonify({"candidates": candidates})
    finally:
        session.close()


@admin_bp.route("/admin", methods=["GET", "POST"])
@login_required
def admin_panel():
    session = get_session()
    try:
        if request.method == "POST":
            action = request.form.get("action", "")
            try:
                if action == "set-unavailable":
                    person = (request.form.get("person") or "").strip()
                    reason = (request.form.get("reason") or "").strip() or None
                    mode = request.form.get("scope") or ""
                    raw_value = (request.form.get("scope_value") or "").strip()
                    value = int(raw_value) if raw_value else None
                    result = admin_service.set_unavailable(
                        session,
                        person,
                        reason,
                        mode=mode,
                        value=value,
                        return_details=True,
                    )
                    if isinstance(result, dict):
                        flash(result.get("message", "Unavailability updated."), "success")
                        replacement_tasks = [
                            row
                            for row in result.get("tasks", [])
                            if row.get("replacements")
                        ]
                        if replacement_tasks:
                            flask_session["replacement_modal"] = {
                                "participant": result.get("participant", person),
                                "scope": result.get("scope", mode),
                                "tasks": replacement_tasks,
                            }
                    else:
                        flash(str(result), "success")
                elif action == "remove-unavailable":
                    record_id = _to_int(request.form.get("record_id"), "Unavailability id")
                    flash(admin_service.remove_unavailable(session, record_id), "success")
                elif action == "set-lead":
                    task_id = _to_int(request.form.get("task_id"), "Task id")
                    person = (request.form.get("person") or "").strip()
                    flash(admin_service.set_lead(session, task_id, person), "success")
                elif action == "remove-assignment":
                    task_id = _to_int(request.form.get("task_id"), "Task id")
                    person = (request.form.get("person") or "").strip()
                    flash(admin_service.remove_assignment(session, task_id, person), "success")
                elif action == "add-helper":
                    task_id = _to_int(request.form.get("task_id"), "Task id")
                    person = (request.form.get("person") or "").strip()
                    flash(admin_service.add_helper(session, task_id, person), "success")
                elif action == "truncate":
                    flash(admin_service.truncate_all(session), "success")
                elif action == "recalculate":
                    messages = run_schedule(session, keep_existing=False)
                    session.commit()
                    for msg in messages:
                        flash(msg, "success")
                else:
                    flash("Unsupported admin action.", "error")
            except ValueError as exc:
                flash(str(exc), "error")
            return redirect(url_for("admin.admin_panel"))

        people = admin_service.list_people(session)
        day_filter_raw = (request.args.get("day") or "").strip()
        try:
            day_filter = int(day_filter_raw) if day_filter_raw else None
        except ValueError:
            day_filter = None
            flash("Day filter must be numeric.", "warning")
        task_options = admin_service.list_tasks(session, day=None)
        task_options, day_options = _future_task_and_day_options(task_options)
        tasks = admin_service.list_tasks(session, day=day_filter)
        unavailabilities = admin_service.list_unavailable(session)
        summary = {
            "participants": session.query(Participant).count(),
            "tasks": session.query(Task).count(),
            "assigned": sum(
                1
                for participant in session.query(Participant).all()
                for assignment in participant.assignments
                if assignment.role in {"lead", "helper"}
            ),
        }
    finally:
        session.close()

    replacement_modal = flask_session.pop("replacement_modal", None)
    from config import SMS_ENABLED

    return render_template(
        "admin.html",
        people=people,
        tasks=tasks,
        task_options=task_options,
        day_options=day_options,
        unavailabilities=unavailabilities,
        day_filter=day_filter,
        replacement_modal=replacement_modal,
        summary=summary,
        sms_enabled=SMS_ENABLED,
    )


def _csv_response(filename: str, content: str) -> Response:
    response = Response(content, mimetype="text/csv")
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@admin_bp.route("/admin/sms/task/<int:task_id>", methods=["POST"])
@login_required
def sms_task(task_id: int):
    import json
    from web.services.sms_service import send_task_reminders
    results = send_task_reminders(task_id)
    return Response(json.dumps(results), mimetype="application/json")


@admin_bp.route("/admin/sms/all", methods=["POST"])
@login_required
def sms_all():
    import json
    from web.services.sms_service import send_all_reminders
    results = send_all_reminders()
    return Response(json.dumps(results), mimetype="application/json")


@admin_bp.route("/admin/recalculate/stream")
@login_required
def recalculate_stream():
    import json

    def generate():
        session = get_session()
        try:
            for assigned, total, msg in run_schedule_stream(session, keep_existing=True):
                payload = json.dumps({"assigned": assigned, "total": total, "msg": msg})
                yield f"data: {payload}\n\n"
        finally:
            session.close()

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@admin_bp.route("/admin/download/schedule")
@login_required
def download_schedule():
    session = get_session()
    try:
        filename, content = generate_schedule_csv(session)
    finally:
        session.close()
    return _csv_response(filename, content)


@admin_bp.route("/admin/download/points")
@login_required
def download_points():
    session = get_session()
    try:
        filename, content = generate_points_csv(session)
    finally:
        session.close()
    return _csv_response(filename, content)


@admin_bp.route("/admin/download/per-person")
@login_required
def download_per_person():
    session = get_session()
    try:
        filename, content = generate_per_person_csv(session)
    finally:
        session.close()
    return _csv_response(filename, content)
