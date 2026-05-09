"""
Celery tasks that talk to the execution-runner service.

The runner is a separate container that spawns ephemeral docker
sandboxes. We never run code inside this Django/Celery process.
"""
from __future__ import annotations

import logging

from celery import shared_task

from services.execution import ExecutionService

logger = logging.getLogger(__name__)


@shared_task(
    name="apps.execution.tasks.run_submission",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 2},
    acks_late=True,
)
def run_submission(self, submission_id: str) -> None:
    """Hand a submission to the execution-runner and persist results."""
    logger.info("run_submission start submission_id=%s", submission_id)
    ExecutionService.run(submission_id)
    logger.info("run_submission done  submission_id=%s", submission_id)
