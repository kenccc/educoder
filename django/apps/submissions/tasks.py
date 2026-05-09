"""Celery task: grade a finished submission."""
from __future__ import annotations

from celery import shared_task

from .models import Submission


@shared_task(name="apps.submissions.tasks.grade_submission")
def grade_submission(submission_id: str) -> None:
    """Grade after execution finishes (called from execution callback)."""
    from services.grading import GradingService

    submission = Submission.objects.select_related("assignment").get(pk=submission_id)
    GradingService.grade(submission)
