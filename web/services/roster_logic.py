"""Shared scheduling helpers for the merged Zomerkamp application."""

from __future__ import annotations

import re
from collections import defaultdict

from models import Assignment, Participant, Task, Unavailability

# ── Group-aware scheduling ────────────────────────────────────────────────────

ONDERBOUW: frozenset[str] = frozenset({"1", "2", "3a", "3b"})
BOVENBOUW: frozenset[str] = frozenset({"4", "5", "6+7", "8"})


def task_group_requirement(task: Task) -> frozenset[str] | None:
    """Return the set of participant groups the task targets, or None if unrestricted.

    Detects:
    - explicit group mention  → "groep 1", "groep 3a", …
    - onderbouw (groepen 1-3b)
    - bovenbouw (groepen 4-8)
    """
    name_lower = task.name.lower()

    # Specific group: "groep 1", "groep 3a", "groep 6+7", …
    m = re.search(r"\bgroep\s+([0-9]+(?:[ab+][0-9]*)?)", name_lower)
    if m:
        raw = m.group(1).strip()
        if raw in ONDERBOUW | BOVENBOUW:
            return frozenset({raw})

    if "onderbouw" in name_lower:
        return ONDERBOUW
    if "bovenbouw" in name_lower:
        return BOVENBOUW

    return None


def _group_score(participant: Participant, task: Task) -> int:
    """0 = matches task group requirement (or no requirement); 1 = requirement exists but no match."""
    required = task_group_requirement(task)
    if required is None:
        return 0
    if participant.group and participant.group in required:
        return 0
    return 1


def compute_total_points(session, include_reserved: bool = True) -> dict[int, int]:
    totals: dict[int, int] = defaultdict(int)
    query = session.query(Assignment).filter(Assignment.role != "backup")
    if not include_reserved:
        query = query.filter(Assignment.is_reserved == False)
    for assignment in query.all():
        totals[assignment.participant_id] += assignment.points_awarded
    return totals


def participant_has_young_children(participant: Participant) -> bool:
    """Check if participant has children in group 1 or 2."""
    if not participant.group:
        return False
    # group field can contain comma-separated groups like "1" or "1,2"
    groups = {g.strip() for g in participant.group.split(",")}
    return bool(groups & {"1", "2"})


def participant_has_groep1_child(participant: Participant) -> bool:
    """Check if participant has a child in groep 1."""
    if not participant.group:
        return False
    groups = {g.strip() for g in participant.group.split(",")}
    return "1" in groups


def task_is_after_20_00(task: Task) -> bool:
    """Check if task ends after 20:00 (8 PM)."""
    return _minutes(task.end_time) > 20 * 60  # 20:00 = 1200 minutes


def task_starts_after_15_30(task: Task) -> bool:
    """Check if task starts at or after 15:30."""
    return _minutes(task.begin_time) >= 15 * 60 + 30  # 15:30 = 930 minutes


def participant_is_available(participant: Participant, task: Task) -> bool:
    if participant.excluded_all_days:
        return False
    return participant.get_block_availability(task.day, task.time_block)


def participant_is_excluded(session, participant_id: int, task: Task) -> bool:
    for record in session.query(Unavailability).filter_by(participant_id=participant_id).all():
        if record.all_days:
            return True
        if record.day == task.day and record.task_id is None:
            return True
        if record.task_id == task.id:
            return True
    return False


def _minutes(value) -> int:
    return value.hour * 60 + value.minute


def participant_has_conflict(session, participant_id: int, task: Task, exclude_task_id: int | None = None) -> bool:
    assignments = session.query(Assignment).join(Task).filter(Assignment.participant_id == participant_id).all()
    for assignment in assignments:
        other = assignment.task
        if exclude_task_id is not None and other.id == exclude_task_id:
            continue
        if other.day != task.day:
            continue
        starts_before_other_ends = _minutes(task.begin_time) < _minutes(other.end_time)
        other_starts_before_task_ends = _minutes(other.begin_time) < _minutes(task.end_time)
        if starts_before_other_ends and other_starts_before_task_ends:
            return True
    return False


def candidate_score(participant: Participant, task: Task, total_points: dict[int, int], prefer_leaders: bool = False) -> tuple:
    # Use TOTAL points (including reserved) for fairness - people with more points shouldn't get more tasks
    current_total = total_points.get(participant.id, 0)
    projected_total = current_total + task.points
    group = _group_score(participant, task)
    
    # Priority for leaders if requested (e.g. when filling a lead slot)
    # Also specifically requested: "for the first day prefer these people as leaders"
    leader_priority = 0
    if prefer_leaders and participant.is_leader:
        # Heavily prefer is_leader people for Day 1 as per user request
        if task.day == 1:
            leader_priority = -2
        else:
            leader_priority = -1
            
    # Fairness FIRST (based on total points including reserved) → then leader priority → group match → name for determinism.
    # This ensures Arthur with 12 reserved points doesn't get additional assignments while others have fewer points.
    return (projected_total, current_total, leader_priority, group, participant.name.lower())


def eligible_candidates(session, task: Task, excluded_ids: set[int] | None = None, prefer_leaders: bool = False) -> list[Participant]:
    excluded_ids = excluded_ids or set()
    # Use TOTAL points (including reserved) for fairness - people with more total work shouldn't get more tasks
    total_points = compute_total_points(session, include_reserved=True)
    candidates = []
    for participant in session.query(Participant).all():
        if participant.id in excluded_ids:
            continue
        if not participant_is_available(participant, task):
            continue
        if participant_is_excluded(session, participant.id, task):
            continue
        if participant_has_conflict(session, participant.id, task, exclude_task_id=task.id):
            continue
        if participant_has_young_children(participant) and task_is_after_20_00(task):
            continue
        if participant_has_groep1_child(participant) and task_starts_after_15_30(task):
            continue
        already_assigned = session.query(Assignment).filter_by(task_id=task.id, participant_id=participant.id).first()
        if already_assigned:
            continue
        candidates.append(participant)
    
    candidates.sort(key=lambda p: candidate_score(p, task, total_points, prefer_leaders=prefer_leaders))
    return candidates