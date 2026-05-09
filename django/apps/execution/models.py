"""Audit log for every execution attempt — useful for incident review."""
from __future__ import annotations

import uuid

from django.db import models


class ExecutionLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission_id = models.UUIDField(db_index=True)
    runner_job_id = models.CharField(max_length=64, blank=True)
    image = models.CharField(max_length=200)
    cpu_limit = models.CharField(max_length=16)
    memory_limit = models.CharField(max_length=16)
    timeout_seconds = models.PositiveIntegerField()
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    exit_code = models.IntegerField(null=True, blank=True)
    timed_out = models.BooleanField(default=False)
