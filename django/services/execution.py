"""ExecutionService: dispatches a submission to execution-runner per testcase,
records TestRun rows, and triggers grading + gamification."""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import httpx
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.db import transaction

from apps.execution.models import ExecutionLog
from apps.exercises.models import Language
from apps.submissions.models import Submission, SubmissionStatus, TestRun

logger = logging.getLogger(__name__)


def _normalize(text: str) -> str:
    """LeetCode-ish normalization: trim trailing whitespace per line, strip ends."""
    return "\n".join(line.rstrip() for line in (text or "").splitlines()).strip()


class ExecutionService:
    @staticmethod
    def run(submission_id: str) -> None:
        submission = (
            Submission.objects
            .select_related("assignment", "assignment__exercise")
            .get(pk=submission_id)
        )

        # Web submissions are graded client-side and posted back via
        # SubmissionService.record_web_result — nothing to run here.
        if submission.assignment.language == Language.WEB:
            ExecutionService._mark_status(submission, SubmissionStatus.PENDING)
            return

        # Retry-safe: skip if a prior attempt already finished, otherwise wipe
        # any partial TestRuns from the prior attempt before re-executing.
        terminal = (SubmissionStatus.SUCCESS, SubmissionStatus.FAILED, SubmissionStatus.TIMEOUT)
        if submission.status in terminal:
            return
        TestRun.objects.filter(submission=submission).delete()

        ExecutionService._mark_status(submission, SubmissionStatus.RUNNING)

        cases = list(submission.assignment.get_test_cases())
        if not cases:
            # No testcases configured: run once with empty stdin, treat any
            # zero exit as success (no grading signal).
            cases = []

        log = ExecutionLog.objects.create(
            submission_id=submission.id,
            image=getattr(settings, "SANDBOX_IMAGE", "educoder/sandbox-python:latest"),
            cpu_limit=str(getattr(settings, "SANDBOX_CPU_LIMIT", "0.5")),
            memory_limit=str(getattr(settings, "SANDBOX_MEMORY_LIMIT", "128m")),
            timeout_seconds=settings.SANDBOX_TIMEOUT_SECONDS,
        )

        passed = 0
        total_runtime = 0
        last_stdout = ""
        last_stderr = ""
        last_exit = None
        timed_out_any = False
        runner_jobs: list[str] = []

        # Run testcases in parallel against execution-runner. Each call is independent
        # (no shared state between sandboxes) so wall time becomes ~max(case_runtime)
        # instead of sum(case_runtime). httpx.Client is thread-safe.
        max_workers = min(8, max(1, len(cases) or 1))
        results_by_idx: dict[int, dict] = {}
        runner_error: list[str] = []

        with httpx.Client(timeout=settings.SANDBOX_TIMEOUT_SECONDS + 10) as client:
            def _call_runner(idx_case):
                idx, case = idx_case
                payload = {
                    "submission_id": str(submission.id),
                    "language": "python",
                    "code": submission.code,
                    "stdin": case.stdin if case else "",
                    "timeout_seconds": settings.SANDBOX_TIMEOUT_SECONDS,
                }
                try:
                    resp = client.post(
                        f"{settings.EXECUTION_RUNNER_URL}/run",
                        json=payload,
                        headers={"Authorization": f"Bearer {settings.EXECUTION_RUNNER_TOKEN}"},
                    )
                    resp.raise_for_status()
                    return idx, resp.json(), None
                except httpx.HTTPError as exc:
                    logger.exception("execution-runner call failed")
                    return idx, None, str(exc)

            iterable = list(enumerate(cases)) if cases else [(0, None)]
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                for idx, result, err in pool.map(_call_runner, iterable):
                    if err:
                        runner_error.append(err)
                    else:
                        results_by_idx[idx] = result

        if runner_error:
            ExecutionService._mark_status(submission, SubmissionStatus.ERROR, stderr=runner_error[0])
            return

        # Reduce results in original order to keep TestRun rows / event order deterministic.
        from apps.realtime.models import EventType
        from services.events import EventService

        iterable = list(enumerate(cases)) if cases else [(0, None)]
        for idx, case in iterable:
            result = results_by_idx.get(idx, {})
            runner_jobs.append(result.get("job_id", ""))
            last_stdout = result.get("stdout", "")
            last_stderr = result.get("stderr", "")
            last_exit = result.get("exit_code")
            total_runtime += int(result.get("duration_ms") or 0)
            if result.get("timed_out"):
                timed_out_any = True

            if case is None:
                continue

            expected = _normalize(case.expected_stdout)
            actual = _normalize(last_stdout)
            ok = (
                not result.get("timed_out")
                and last_exit == 0
                and expected == actual
            )
            if ok:
                passed += 1

            TestRun.objects.create(
                submission=submission,
                test_case=case,
                name=case.name,
                is_hidden=case.is_hidden,
                passed=ok,
                actual_stdout=last_stdout,
                expected_stdout=case.expected_stdout,
                error=last_stderr if not ok else "",
                runtime_ms=result.get("duration_ms"),
            )

            EventService.record(
                user=submission.student,
                assignment=submission.assignment,
                attempt=submission.attempt,
                type=(EventType.TESTCASE_PASS if ok else EventType.TESTCASE_FAIL).value,
                payload={
                    "case": case.name,
                    "is_hidden": case.is_hidden,
                    "submission_id": str(submission.id),
                    "runtime_ms": result.get("duration_ms"),
                },
            )

        with transaction.atomic():
            submission.stdout = last_stdout
            submission.stderr = last_stderr
            submission.exit_code = last_exit
            submission.duration_ms = total_runtime
            submission.completed_at = datetime.now(timezone.utc)
            submission.passed_count = passed
            submission.total_count = len(cases)

            if timed_out_any and len(cases) == 0:
                submission.status = SubmissionStatus.TIMEOUT
            elif len(cases) == 0:
                submission.status = SubmissionStatus.SUCCESS if last_exit == 0 else SubmissionStatus.FAILED
            else:
                submission.status = (
                    SubmissionStatus.SUCCESS if passed == len(cases) else SubmissionStatus.FAILED
                )

            submission.save()

            log.runner_job_id = ",".join(runner_jobs)[:64]
            log.exit_code = last_exit
            log.timed_out = timed_out_any
            log.finished_at = submission.completed_at
            log.save()

        # Grade + award synchronously here — we're already in the execution worker.
        # Two prior `.delay()` hops added queue latency (often >500ms each) for no benefit.
        from services.gamification import GamificationService
        from services.grading import GradingService
        GradingService.grade(submission)
        submission.refresh_from_db()
        GamificationService.award_for_submission(str(submission.id))
        submission.refresh_from_db()

        ExecutionService._broadcast(submission)

        from apps.realtime.models import EventType
        from services.events import EventService
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
                "duration_ms": submission.duration_ms,
                "xp_earned": submission.xp_earned,
            },
        )

    # ---- helpers ----
    @staticmethod
    def _mark_status(submission: Submission, status: str, *, stderr: str = "") -> None:
        submission.status = status
        if stderr:
            submission.stderr = stderr
            submission.completed_at = datetime.now(timezone.utc)
        submission.save(update_fields=["status", "stderr", "completed_at"])
        ExecutionService._broadcast(submission)

    @staticmethod
    def _broadcast(submission: Submission) -> None:
        layer = get_channel_layer()
        if layer is None:
            return
        async_to_sync(layer.group_send)(
            f"submission_{submission.id}",
            {
                "type": "submission.update",
                "payload": {
                    "id": str(submission.id),
                    "status": submission.status,
                    "exit_code": submission.exit_code,
                    "passed": submission.passed_count,
                    "total": submission.total_count,
                },
            },
        )
        if submission.assignment.classroom_id:
            async_to_sync(layer.group_send)(
                f"classroom_{submission.assignment.classroom_id}",
                {
                    "type": "classroom.event",
                    "payload": {
                        "kind": "submission",
                        "student": submission.student.username,
                        "assignment_id": submission.assignment_id,
                        "status": submission.status,
                        "passed": submission.passed_count,
                        "total": submission.total_count,
                    },
                },
            )
