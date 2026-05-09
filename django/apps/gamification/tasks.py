"""Celery task: award XP/badges after a successful submission."""
from __future__ import annotations

from celery import shared_task


@shared_task(name="apps.gamification.tasks.award_for_submission")
def award_for_submission(submission_id: str) -> None:
    from services.gamification import GamificationService
    GamificationService.award_for_submission(submission_id)
