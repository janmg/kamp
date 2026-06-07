"""Read-only dashboard views."""

from __future__ import annotations

from collections import defaultdict

from flask import Blueprint, render_template, request
from sqlalchemy.orm import joinedload

from models import Assignment, Participant, Task, get_session
from roster_logic import compute_total_points
from web.auth import login_required

MESSAGING_APPS = ["whatsapp", "signal", "telegram", "sms", "none"]
GROUPS = ["1", "2", "3a", "3b", "4", "5", "6+7", "8"]

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    from flask import redirect, url_for
    return redirect(url_for("dashboard.master"))


@dashboard_bp.route("/leaderboard")
@login_required
def leaderboard():
    session = get_session()
    try:
        totals = compute_total_points(session)
        # Eager load assignments to avoid N+1 queries
        participants = sorted(
            session.query(Participant).options(
                joinedload(Participant.assignments)
            ).all(),
            key=lambda participant: (totals.get(participant.id, 0), participant.name.lower()),
            reverse=True
        )
        rows = []
        for rank, participant in enumerate(participants, start=1):
            active_tasks = sum(1 for assignment in participant.assignments if assignment.role in {"lead", "helper"})
            rows.append(
                {
                    "rank": rank,
                    "name": participant.name,
                    "email": participant.email,
                    "phone": participant.phone or "-",
                    "messaging": participant.messaging or "whatsapp",
                    "remarks": participant.remarks or "-",
                    "points": totals.get(participant.id, 0),
                    "task_count": active_tasks,
                }
            )
    finally:
        session.close()

    return render_template("leaderboard.html", rows=rows)


@dashboard_bp.route("/schedule")
@login_required
def schedule():
    session = get_session()
    try:
        totals = compute_total_points(session)
        # Eager load assignments and tasks to avoid N+1 queries
        participants = sorted(
            session.query(Participant).options(
                joinedload(Participant.assignments).joinedload(Assignment.task).joinedload(Task.assignments).joinedload(Assignment.participant)
            ).all(),
            key=lambda person: person.name.lower()
        )
        people = []
        for participant in participants:
            total_points = totals.get(participant.id, 0)
            # Skip participants with zero points (not assigned to any tasks)
            if total_points == 0:
                continue
            
            tasks = []
            visible_assignments = [assignment for assignment in participant.assignments if assignment.role in {"lead", "helper"}]
            for assignment in sorted(visible_assignments, key=lambda item: (item.task.day, item.task.begin_time, item.task.name)):
                task_assignments = assignment.task.assignments
                task_lead = next((a.participant.name for a in task_assignments if a.role == "lead" and a.participant_id != participant.id), None)
                task_helpers = [a.participant.name for a in task_assignments if a.role == "helper" and a.participant_id != participant.id]
                tasks.append(
                    {
                        "day": assignment.task.day,
                        "begin": assignment.task.begin_time.strftime("%H:%M"),
                        "end": assignment.task.end_time.strftime("%H:%M"),
                        "name": assignment.task.name,
                        "block": assignment.task.time_block,
                        "role": assignment.role,
                        "points": assignment.points_awarded,
                        "task_lead": task_lead,
                        "task_helpers": task_helpers,
                        "location": assignment.task.location,
                        "description": assignment.task.description,
                    }
                )
            people.append(
                {
                    "name": participant.name,
                    "email": participant.email,
                    "phone": participant.phone or "-",
                    "messaging": participant.messaging or "whatsapp",
                    "remarks": participant.remarks or "-",
                    "total_points": total_points,
                    "tasks": tasks,
                }
            )
    finally:
        session.close()

    name_filter = request.args.get("name", "").strip()
    from config import PUBLIC_URL
    return render_template("schedule.html", people=people, name_filter=name_filter, public_url=PUBLIC_URL)


@dashboard_bp.route("/master")
@login_required
def master():
    from datetime import date, datetime as dt, timedelta

    session = get_session()
    try:
        current_year = date.today().year
        day_origin = date(2026, 6, 3) if current_year == 2026 else date(current_year, 1, 1)

        by_day: dict[int, list] = defaultdict(list)
        # Eager load assignments and participants to avoid N+1 queries
        tasks = session.query(Task).options(
            joinedload(Task.assignments).joinedload(Assignment.participant)
        ).order_by(Task.day, Task.begin_time, Task.name).all()
        
        for task in tasks:
            assignments = sorted(task.assignments, key=lambda item: (["lead", "helper", "backup"].index(item.role), item.participant.name.lower()))
            active_assignments = [assignment for assignment in assignments if assignment.role in {"lead", "helper"}]
            task_date = day_origin + timedelta(days=task.day - 1)
            end_iso = dt.combine(task_date, task.end_time).strftime("%Y-%m-%dT%H:%M:00")
            by_day[task.day].append(
                {
                    "id": task.id,
                    "name": task.name,
                    "begin": task.begin_time.strftime("%H:%M"),
                    "end": task.end_time.strftime("%H:%M"),
                    "end_iso": end_iso,
                    "points": task.points,
                    "people_required": task.people_required,
                    "time_block": task.time_block,
                    "assignment_count": len(active_assignments),
                    "lead": next((assignment for assignment in assignments if assignment.role == "lead"), None),
                    "helpers": [assignment for assignment in assignments if assignment.role == "helper"],
                    "location": task.location,
                    "description": task.description,
                }
            )
    finally:
        session.close()

    return render_template("master.html", by_day=dict(sorted(by_day.items())))


@dashboard_bp.route("/api/tasks")
@login_required
def api_tasks():
    from flask import jsonify

    session = get_session()
    try:
        tasks = session.query(Task).options(
            joinedload(Task.assignments).joinedload(Assignment.participant)
        ).order_by(Task.day, Task.begin_time, Task.name).all()

        result = []
        for task in tasks:
            lead_assignment = next(
                (a for a in task.assignments if a.role == "lead"), None
            )
            helpers = [
                a for a in task.assignments if a.role == "helper"
            ]
            result.append(
                {
                    "id": task.id,
                    "name": task.name,
                    "description": task.description,
                    "location": task.location,
                    "day": task.day,
                    "begin": task.begin_time.strftime("%H:%M"),
                    "end": task.end_time.strftime("%H:%M"),
                    "lead": lead_assignment.participant.name if lead_assignment else None,
                    "helpers": [a.participant.name for a in helpers],
                }
            )
    finally:
        session.close()

    return jsonify(result)


@dashboard_bp.route("/participants", methods=["GET", "POST"])
@login_required
def participants():
    from web.auth import is_admin
    
    session = get_session()
    try:
        if request.method == "POST":
            # Only admins can update participant details via this route
            if not is_admin():
                return "Forbidden", 403
                
            participant_id = request.form.get("participant_id", type=int)
            messaging = request.form.get("messaging", "whatsapp")
            if messaging not in MESSAGING_APPS:
                messaging = "whatsapp"
            raw_group = request.form.get("group") or ""
            group = ",".join(g for g in raw_group.split(",") if g in GROUPS) or None
            if participant_id:
                person = session.get(Participant, participant_id)
                if person:
                    person.messaging = messaging
                    person.group = group
                    session.commit()

        people = [
            {
                "id": p.id,
                "name": p.name,
                "email": p.email,
                "phone": p.phone or "-",
                "messaging": p.messaging if p.messaging else "whatsapp",
                "group": p.group or "",
            }
            for p in sorted(session.query(Participant).all(), key=lambda p: p.name.lower())
        ]
    finally:
        session.close()

    from config import PUBLIC_URL
    return render_template("participants.html", people=people, messaging_apps=MESSAGING_APPS, groups=GROUPS, public_url=PUBLIC_URL, is_admin=is_admin())
