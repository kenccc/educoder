from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models

from apps.assignments.models import Assignment, AssignmentAttempt
from apps.exercises.models import TestCase


class SubmissionStatus(models.TextChoices):
    PENDING  = "pending",  "Pending"
    RUNNING  = "running",  "Running"
    SUCCESS  = "success",  "Success"
    FAILED   = "failed",   "Failed"
    TIMEOUT  = "timeout",  "Timeout"
    ERROR    = "error",    "Error"


class Submission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions")
    attempt = models.ForeignKey(
        AssignmentAttempt,
        on_delete=models.CASCADE,
        related_name="submissions",
        null=True,
        blank=True,
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    code = models.TextField()
    status = models.CharField(max_length=16, choices=SubmissionStatus.choices, default=SubmissionStatus.PENDING)

    stdout = models.TextField(blank=True)
    stderr = models.TextField(blank=True)
    exit_code = models.IntegerField(null=True, blank=True)
    duration_ms = models.PositiveIntegerField(null=True, blank=True)

    score = models.PositiveIntegerField(null=True, blank=True)
    is_correct = models.BooleanField(null=True, blank=True)
    passed_count = models.PositiveIntegerField(default=0)
    total_count = models.PositiveIntegerField(default=0)
    xp_awarded = models.BooleanField(default=False)
    xp_earned = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("assignment", "student")),
            models.Index(fields=("status",)),
            models.Index(fields=("attempt",)),
        ]


class TestRun(models.Model):
    """Per-testcase result for a single submission. LeetCode-style."""

    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name="test_runs")
    test_case = models.ForeignKey(TestCase, on_delete=models.CASCADE, related_name="runs", null=True, blank=True)
    name = models.CharField(max_length=120)
    is_hidden = models.BooleanField(default=False)
    passed = models.BooleanField(default=False)
    actual_stdout = models.TextField(blank=True)
    expected_stdout = models.TextField(blank=True)
    error = models.TextField(blank=True)
    runtime_ms = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ("id",)
