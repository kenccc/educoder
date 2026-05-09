from __future__ import annotations

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.assignments.models import Assignment, AssignmentAttempt, AttemptStatus
from apps.exercises.models import Language
from apps.submissions.models import Submission, SubmissionStatus, TestRun


class AttemptService:
    @staticmethod
    def get_or_create(*, assignment: Assignment, student) -> AssignmentAttempt:
        if not assignment.is_open():
            raise ValidationError("This assignment is not open right now.")
        with transaction.atomic():
            attempt = (
                AssignmentAttempt.objects
                .select_for_update()
                .filter(assignment=assignment, student=student, status=AttemptStatus.ACTIVE)
                .order_by("-started_at")
                .first()
            )
            if attempt and attempt.is_expired():
                attempt.status = AttemptStatus.EXPIRED
                attempt.ended_at = timezone.now()
                attempt.save(update_fields=["status", "ended_at"])
                _emit_attempt_event(attempt, "attempt_end", reason="expired")
                attempt = None
            if not attempt:
                if assignment.max_attempts:
                    count = AssignmentAttempt.objects.filter(
                        assignment=assignment, student=student
                    ).exclude(status=AttemptStatus.ACTIVE).count()
                    if count >= assignment.max_attempts:
                        raise PermissionDenied("Attempt limit reached.")
                try:
                    attempt = AssignmentAttempt.objects.create(
                        assignment=assignment, student=student
                    )
                    _emit_attempt_event(attempt, "attempt_start")
                except IntegrityError:
                    # Lost the race against the unique-active constraint.
                    attempt = (
                        AssignmentAttempt.objects
                        .filter(
                            assignment=assignment,
                            student=student,
                            status=AttemptStatus.ACTIVE,
                        )
                        .order_by("-started_at")
                        .first()
                    )
                    if attempt is None:
                        raise
            return attempt

    @staticmethod
    def submit(attempt: AssignmentAttempt) -> None:
        attempt.status = AttemptStatus.SUBMITTED
        attempt.ended_at = timezone.now()
        attempt.save(update_fields=["status", "ended_at"])
        _emit_attempt_event(attempt, "attempt_end", reason="submitted")

    @staticmethod
    def terminate(attempt: AssignmentAttempt, reason: str = "") -> None:
        attempt.status = AttemptStatus.TERMINATED
        attempt.ended_at = timezone.now()
        attempt.save(update_fields=["status", "ended_at"])
        _emit_attempt_event(attempt, "attempt_end", reason=reason or "terminated")


def _emit_attempt_event(attempt: AssignmentAttempt, event_type: str, **payload) -> None:
    from apps.realtime.models import EventType
    from services.events import EventService
    if event_type not in EventType.values:
        return
    EventService.record(
        user=attempt.student,
        assignment=attempt.assignment,
        attempt=attempt,
        type=event_type,
        payload=payload,
    )


class SubmissionService:
    @staticmethod
    def create_and_dispatch(*, assignment: Assignment, student, code: str, attempt: AssignmentAttempt | None = None) -> Submission:
        if not (code or "").strip():
            raise ValueError("empty submission")

        if attempt is None:
            attempt = AttemptService.get_or_create(assignment=assignment, student=student)

        if attempt.is_expired():
            AttemptService.terminate(attempt, reason="time-up")
            raise PermissionDenied("Time is up for this attempt.")

        with transaction.atomic():
            submission = Submission.objects.create(
                assignment=assignment,
                student=student,
                code=code,
                attempt=attempt,
            )
            attempt.submission_count = (attempt.submission_count or 0) + 1
            attempt.save(update_fields=["submission_count"])

        from apps.realtime.models import CodeSnapshot, EventType, SnapshotTrigger
        from services.events import EventService
        CodeSnapshot.objects.create(
            attempt=attempt, code=code, trigger=SnapshotTrigger.RUN.value
        )
        EventService.record(
            user=student,
            assignment=assignment,
            attempt=attempt,
            type=EventType.RUN_CODE.value,
            payload={"submission_id": str(submission.id), "code_len": len(code)},
        )

        # Web submissions are graded in-browser via record_web_result.
        # Skip the Celery dispatch — otherwise the worker would stomp the
        # final status back to PENDING via _mark_status.
        if assignment.language != Language.WEB:
            from apps.execution.tasks import run_submission
            run_submission.delay(str(submission.id))
        return submission

    @staticmethod
    def record_web_result(*, submission: Submission, results: list[dict]) -> None:
        """Receive client-side iframe assertion results and persist as TestRuns.
        results: [{"name": str, "passed": bool, "is_hidden": bool, "error": str}]
        """
        from datetime import datetime, timezone as _tz

        # Idempotency: only the first POST grades. Repeated calls (refresh,
        # double-submit) must not stack TestRuns or re-award XP.
        with transaction.atomic():
            locked = (
                Submission.objects.select_for_update()
                .filter(pk=submission.pk, status=SubmissionStatus.PENDING)
                .first()
            )
            if locked is None:
                return
            submission = locked

            passed = sum(1 for r in results if r.get("passed"))
            for r in results:
                TestRun.objects.create(
                    submission=submission,
                    name=r.get("name", "case"),
                    is_hidden=bool(r.get("is_hidden", False)),
                    passed=bool(r.get("passed")),
                    actual_stdout=r.get("actual") or "",
                    expected_stdout=r.get("expected") or "",
                    error=r.get("error") or "",
                )
            submission.passed_count = passed
            submission.total_count = len(results)
            submission.completed_at = datetime.now(_tz.utc)
            submission.status = (
                SubmissionStatus.SUCCESS if passed == len(results) and results else SubmissionStatus.FAILED
            )
            submission.save()

        from apps.realtime.models import EventType
        from services.events import EventService
        for r in results:
            ok = bool(r.get("passed"))
            EventService.record(
                user=submission.student,
                assignment=submission.assignment,
                attempt=submission.attempt,
                type=(EventType.TESTCASE_PASS if ok else EventType.TESTCASE_FAIL).value,
                payload={
                    "case": r.get("name", "case"),
                    "is_hidden": bool(r.get("is_hidden", False)),
                    "submission_id": str(submission.id),
                    "error": (r.get("error") or "")[:500] if not ok else "",
                },
            )
        EventService.record(
            user=submission.student,
            assignment=submission.assignment,
            attempt=submission.attempt,
            type=EventType.SUBMISSION.value,
            payload={
                "submission_id": str(submission.id),
                "status": submission.status,
                "passed": submission.passed_count,
                "total": submission.total_count,
            },
        )

        # Web grading runs in-browser already; grade + award synchronously so the
        # response reflects final score/XP. (Python path stays async via Celery.)
        from services.grading import GradingService
        from services.gamification import GamificationService
        GradingService.grade(submission)
        submission.refresh_from_db()
        GamificationService.award_for_submission(str(submission.id))


def is_web(assignment: Assignment) -> bool:
    return assignment.language == Language.WEB
