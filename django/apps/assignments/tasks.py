"""Aggregate per-assignment teacher metrics — runs every 5 minutes."""
from __future__ import annotations

import logging
import re
import statistics
from collections import Counter

from celery import shared_task
from django.db.models import Count, Q
from django.utils import timezone

logger = logging.getLogger(__name__)


_PY_EXC_RE = re.compile(r"^(?P<exc>[A-Z][A-Za-z_]*Error|Exception|KeyboardInterrupt)\b", re.MULTILINE)


@shared_task(name="apps.assignments.tasks.aggregate_assignment_metrics")
def aggregate_assignment_metrics(assignment_ids: list[int] | None = None) -> int:
    """Recompute AssignmentMetrics rows. Returns number updated.

    If `assignment_ids` is None, scans every published assignment.
    """
    from apps.assignments.models import (
        Assignment,
        AssignmentAttempt,
        AssignmentMetrics,
        AttemptStatus,
    )
    from apps.exercises.models import HintReveal
    from apps.submissions.models import Submission, SubmissionStatus, TestRun

    qs = Assignment.objects.filter(is_published=True)
    if assignment_ids:
        qs = qs.filter(pk__in=assignment_ids)

    updated = 0
    for assignment in qs.iterator():
        attempts = AssignmentAttempt.objects.filter(assignment=assignment)
        students_started = attempts.values("student_id").distinct().count()

        completed = attempts.filter(
            Q(status__in=(AttemptStatus.SUBMITTED,)) | Q(is_correct=True)
        ).values("student_id").distinct().count()
        completion_rate = (completed / students_started) if students_started else 0.0

        # Median solve time = (best_correct_submission.completed_at - attempt.started_at)
        solve_seconds: list[int] = []
        for a in attempts.filter(is_correct=True).select_related().iterator():
            best = (
                Submission.objects
                .filter(attempt=a, is_correct=True)
                .order_by("completed_at")
                .first()
            )
            if best and best.completed_at and a.started_at:
                solve_seconds.append(int((best.completed_at - a.started_at).total_seconds()))
        median_solve = int(statistics.median(solve_seconds)) if solve_seconds else 0

        avg_runs = (
            attempts.aggregate(avg=Count("submissions"))["avg"]
            if attempts.exists() else 0
        )
        # `avg_runs` above mis-aggregates; recompute as a real average.
        run_counts = list(
            attempts.values("id").annotate(n=Count("submissions")).values_list("n", flat=True)
        )
        avg_runs = (sum(run_counts) / len(run_counts)) if run_counts else 0.0

        # Hint usage — fraction of attempts with at least one HintReveal.
        attempts_with_hint = (
            HintReveal.objects.filter(attempt__assignment=assignment)
            .values("attempt_id").distinct().count()
        )
        hint_usage_pct = (attempts_with_hint / attempts.count()) if attempts.exists() else 0.0

        # Most failed test (visible+hidden, joined via TestRun.test_case).
        failed = (
            TestRun.objects
            .filter(submission__assignment=assignment, passed=False, test_case__isnull=False)
            .values("test_case_id")
            .annotate(n=Count("id"))
            .order_by("-n")[:1]
        )
        most_failed_test_id = failed[0]["test_case_id"] if failed else None

        common_errors = _common_errors(assignment)

        AssignmentMetrics.objects.update_or_create(
            assignment=assignment,
            defaults={
                "students_started": students_started,
                "students_completed": completed,
                "completion_rate": round(completion_rate, 3),
                "median_solve_seconds": median_solve,
                "avg_runs": round(avg_runs, 2),
                "hint_usage_pct": round(hint_usage_pct, 3),
                "most_failed_test_id": most_failed_test_id,
                "common_errors": common_errors,
            },
        )
        updated += 1

    return updated


def _common_errors(assignment) -> list[dict]:
    """Cluster errors via three signals: stderr exception class, failed testcase name, raw stderr first-line."""
    from apps.submissions.models import Submission, TestRun

    bucket: Counter = Counter()

    failed_runs = (
        TestRun.objects
        .filter(submission__assignment=assignment, passed=False)
        .values("name", "error")
    )
    for r in failed_runs:
        # Failed testcase name is always informative.
        bucket[("test", r["name"])] += 1
        err = (r.get("error") or "").strip()
        if err:
            m = _PY_EXC_RE.search(err)
            if m:
                bucket[("exc", m.group("exc"))] += 1

    # Top-level submission stderr too (covers SyntaxError before tests run).
    stderr_lines = (
        Submission.objects
        .filter(assignment=assignment)
        .exclude(stderr="")
        .values_list("stderr", flat=True)
    )
    for s in stderr_lines:
        m = _PY_EXC_RE.search(s)
        if m:
            bucket[("exc", m.group("exc"))] += 1

    most = bucket.most_common(8)
    return [
        {"label": _label(kind, value), "count": n, "kind": kind, "value": value}
        for (kind, value), n in most
    ]


def _label(kind: str, value: str) -> str:
    if kind == "exc":
        return f"{value} (exception)"
    if kind == "test":
        return f"Test failed: {value}"
    return value
