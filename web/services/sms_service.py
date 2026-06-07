"""Twilio SMS reminder service.

SMS sending is disabled by default. Set the following environment variables
(or add them to your .env file) to enable:

    TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    TWILIO_AUTH_TOKEN=your_auth_token
    TWILIO_FROM=+12015551234   # your Twilio phone number in E.164 format

Register at: https://www.twilio.com/try-twilio
"""

from __future__ import annotations

from config import SMS_ENABLED, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM
from models import Assignment, Task, get_session

DAY_NAMES = {1: "woensdag", 2: "donderdag", 3: "vrijdag", 4: "zaterdag"}


def _normalise_phone(raw: str) -> str:
    """Normalize phone numbers: handle Excel dots, replace +358, handle missing leading zero."""
    if not raw:
        return raw

    # Remove everything from the first dot onwards (common in Excel CSV exports)
    raw = str(raw).split(".")[0]

    # Remove dashes and spaces
    digits = raw.strip().replace(" ", "").replace("-", "")
    # Replace +358 with 0 (Finnish format)
    if digits.startswith("+358"):
        digits = "0" + digits[4:]

    # If a phone number starts with a 4, assume a leading zero is missing
    if digits.startswith("4"):
        digits = "0" + digits

    return digits


def _build_message(participant_name: str, role: str, task_name: str, day: int, begin: str, end: str) -> str:
    day_nl = DAY_NAMES.get(day, f"dag {day}")
    role_nl = "teamleider" if role == "lead" else "helper"
    return (
        f"Hallo {participant_name}, herinnering: jij bent ingepland als {role_nl} "
        f"voor '{task_name}' op {day_nl} van {begin} tot {end}. "
        f"Bedankt voor je hulp! — NTC Zomerkamp"
    )


def send_sms(to: str, body: str) -> dict:
    """Send a single SMS. Returns a result dict with 'ok', 'sid', and 'error'."""
    if not SMS_ENABLED:
        return {"ok": False, "error": "SMS not configured — set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM"}
    try:
        from twilio.rest import Client  # imported lazily so missing package doesn't break startup
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(to=to, from_=TWILIO_FROM, body=body)
        return {"ok": True, "sid": message.sid, "error": None}
    except Exception as exc:
        return {"ok": False, "sid": None, "error": str(exc)}


def send_task_reminders(task_id: int) -> list[dict]:
    """Send SMS reminders to all lead+helper participants of a task.

    Returns a list of result dicts per participant:
        {"name": str, "phone": str, "ok": bool, "error": str|None}
    """
    session = get_session()
    try:
        task = session.get(Task, task_id)
        if task is None:
            return [{"name": "-", "phone": "-", "ok": False, "error": f"Task {task_id} not found"}]

        begin = task.begin_time.strftime("%H:%M")
        end = task.end_time.strftime("%H:%M")
        results = []

        active = [a for a in task.assignments if a.role in {"lead", "helper"}]
        if not active:
            return [{"name": "-", "phone": "-", "ok": False, "error": "No assigned participants for this task"}]

        for assignment in active:
            p = assignment.participant
            if not p.phone:
                results.append({"name": p.name, "phone": "-", "ok": False, "error": "No phone number"})
                continue
            phone = _normalise_phone(p.phone)
            body = _build_message(p.name, assignment.role, task.name, task.day, begin, end)
            result = send_sms(phone, body)
            results.append({"name": p.name, "phone": phone, "ok": result["ok"], "error": result.get("error")})

        return results
    finally:
        session.close()


def send_all_reminders() -> list[dict]:
    """Send reminders for every task to all assigned participants."""
    session = get_session()
    try:
        tasks = session.query(Task).order_by(Task.day, Task.begin_time).all()
        task_ids = [t.id for t in tasks]
    finally:
        session.close()

    all_results = []
    for task_id in task_ids:
        all_results.extend(send_task_reminders(task_id))
    return all_results
