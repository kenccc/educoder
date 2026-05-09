"""Status engine — heuristics over recent ClassroomEvent rows.

Refreshes StudentStatus every 30s (Celery beat). Pushes status_change
broadcasts to teacher dashboards when a status flips.
"""
from __future__ import annotations

import logging
from collections import Counter, defaultdict
from datetime import timedelta

from celery import shared_task
from django.db.models import Q
from django.utils import timezone

logger = logging.getLogger(__name__)


# Tunables
IDLE_AFTER_SECONDS       = 10 * 60   # no run for 10m → idle
STUCK_REPEATED_ERRORS    = 3         # 3+ identical fails in a row → stuck
STRUGGLING_FAILED_RUNS   = 10        # 10+ failed runs since last pass → struggling
LOOKBACK_WINDOW_MINUTES  = 60        # we only consider activity within last 60m
PROGRESSING_RECENT_PASS  = 5 * 60    # last_pass within 5m & no recent fails → progressing


@shared_task(name="apps.realtime.tasks.compute_student_status")
def compute_student_status() -> int:
    """Recompute StudentStatus rows. Returns number of statuses changed."""
    from apps.assignments.models import AssignmentAttempt, AttemptStatus
    from apps.classrooms.models import Membership
    from apps.realtime.models import (
        ClassroomEvent,
        EventType,
        StudentStatus,
        StudentStatusKind,
    )
    from services.events import EventService

    now = timezone.now()
    window_start = now - timedelta(minutes=LOOKBACK_WINDOW_MINUTES)

    # Active attempts drive the dashboard. Anyone in a classroom but without
    # an active attempt → "offline" / "idle" depending on presence events.
    active_attempts = (
        AssignmentAttempt.objects
        .filter(status=AttemptStatus.ACTIVE)
        .select_related("assignment", "assignment__classroom", "student")
    )

    # All recent events grouped by user — a single query feeds every heuristic.
    recent = (
        ClassroomEvent.objects
        .filter(created_at__gte=window_start)
        .order_by("user_id", "created_at")
        .values("user_id", "type", "payload", "created_at", "attempt_id", "assignment_id", "classroom_id")
    )
    by_user: dict[int, list[dict]] = defaultdict(list)
    for row in recent:
        by_user[row["user_id"]].append(row)

    changed = 0
    seen_user_ids: set[int] = set()

    for attempt in active_attempts:
        events = by_user.get(attempt.student_id, [])
        seen_user_ids.add(attempt.student_id)

        last_run = _last_event_at(events, EventType.RUN_CODE)
        last_pass = _last_event_at(events, EventType.TESTCASE_PASS)
        last_fail = _last_event_at(events, EventType.TESTCASE_FAIL)
        last_activity = _last_any(events) or attempt.started_at

        repeated_errors = _max_repeated_error_streak(events)
        failed_runs_since_progress = _failed_runs_since_progress(events)
        minutes_no_progress = _minutes_since(now, last_pass or attempt.started_at)
        progress = _progress_fraction(events)

        stuck_score = (
            repeated_errors * 3.0
            + minutes_no_progress * 1.0
            + failed_runs_since_progress * 0.5
        )

        # Heuristic ladder — order matters.
        if last_run and (now - last_run).total_seconds() <= PROGRESSING_RECENT_PASS and (
            last_pass is not None
            and (now - last_pass).total_seconds() <= PROGRESSING_RECENT_PASS
            and (last_fail is None or last_pass >= last_fail)
        ):
            kind = StudentStatusKind.PROGRESSING
        elif last_run is None or (now - last_run).total_seconds() >= IDLE_AFTER_SECONDS:
            kind = StudentStatusKind.IDLE
        elif repeated_errors >= STUCK_REPEATED_ERRORS:
            kind = StudentStatusKind.STUCK
        elif failed_runs_since_progress >= STRUGGLING_FAILED_RUNS:
            kind = StudentStatusKind.STRUGGLING
        else:
            kind = StudentStatusKind.ONLINE

        status, _ = StudentStatus.objects.select_related("student").get_or_create(
            student=attempt.student,
        )
        prior_kind = status.status
        status.classroom = attempt.assignment.classroom
        status.active_assignment = attempt.assignment
        status.active_attempt = attempt
        status.status = kind.value
        status.stuck_score = round(stuck_score, 2)
        status.last_activity = last_activity
        status.last_run_at = last_run
        status.last_pass_at = last_pass
        status.progress = progress
        status.save()

        if prior_kind != kind.value:
            changed += 1
            EventService.record(
                user=attempt.student,
                classroom=attempt.assignment.classroom,
                assignment=attempt.assignment,
                attempt=attempt,
                type=EventType.STATUS_CHANGE.value,
                payload={"from": prior_kind, "to": kind.value, "stuck_score": status.stuck_score},
            )
            EventService.broadcast_status(status)

    # Mark students who lost their active attempt as offline (drift cleanup).
    drift = StudentStatus.objects.exclude(student_id__in=seen_user_ids).exclude(
        status=StudentStatusKind.OFFLINE
    )
    for status in drift:
        prior_kind = status.status
        status.status = StudentStatusKind.OFFLINE.value
        status.active_assignment = None
        status.active_attempt = None
        status.save(update_fields=["status", "active_assignment", "active_attempt", "updated_at"])
        if prior_kind != status.status:
            changed += 1
            EventService.broadcast_status(status)

    return changed


# ---------- helpers ----------

def _last_event_at(events: list[dict], type_value: str):
    for ev in reversed(events):
        if ev["type"] == type_value:
            return ev["created_at"]
    return None


def _last_any(events: list[dict]):
    return events[-1]["created_at"] if events else None


def _minutes_since(now, ts) -> float:
    if ts is None:
        return 9999.0
    return max(0.0, (now - ts).total_seconds() / 60.0)


def _max_repeated_error_streak(events: list[dict]) -> int:
    """Longest run of consecutive testcase_fail events with the same `case` payload."""
    streak = 0
    best = 0
    last_key = None
    for ev in events:
        if ev["type"] != "testcase_fail":
            continue
        key = (ev.get("payload") or {}).get("case")
        if key is not None and key == last_key:
            streak += 1
        else:
            streak = 1
            last_key = key
        best = max(best, streak)
    return best


def _failed_runs_since_progress(events: list[dict]) -> int:
    """Count testcase_fail events since the last testcase_pass."""
    count = 0
    for ev in events:
        if ev["type"] == "testcase_pass":
            count = 0
        elif ev["type"] == "testcase_fail":
            count += 1
    return count


def _progress_fraction(events: list[dict]) -> float:
    """Best fraction observed across SUBMISSION events in the window."""
    best = 0.0
    for ev in events:
        if ev["type"] != "submission":
            continue
        p = ev.get("payload") or {}
        total = p.get("total") or 0
        passed = p.get("passed") or 0
        if total:
            best = max(best, passed / total)
    return round(best, 3)
