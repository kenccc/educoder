"""Grading: derive pass/fail + score from TestRuns and update best_score on attempt."""
from __future__ import annotations

from django.db import transaction

from apps.submissions.models import Submission, SubmissionStatus


class GradingService:
    @staticmethod
    def grade(submission: Submission) -> None:
        total = submission.total_count or 0
        passed = submission.passed_count or 0

        if total == 0:
            # No testcases → can only signal exec success vs fail
            submission.is_correct = submission.status == SubmissionStatus.SUCCESS
            submission.score = (
                submission.assignment.max_points if submission.is_correct else 0
            )
        else:
            submission.is_correct = passed == total
            submission.score = int(
                round((passed / total) * submission.assignment.max_points)
            )

        submission.save(update_fields=["is_correct", "score"])

        attempt = submission.attempt
        if attempt:
            with transaction.atomic():
                attempt = type(attempt).objects.select_for_update().get(pk=attempt.pk)
                if (submission.score or 0) > attempt.best_score:
                    attempt.best_score = submission.score or 0
                if submission.is_correct:
                    attempt.is_correct = True
                attempt.save(update_fields=["best_score", "is_correct"])
