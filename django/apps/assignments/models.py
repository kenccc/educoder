from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.classrooms.models import Classroom
from apps.exercises.models import Exercise, Language


class Assignment(models.Model):
    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.CASCADE,
        related_name="assignments",
        null=True,
        blank=True,
        help_text="Null = student-owned solo practice (see solo_owner).",
    )
    solo_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="solo_assignments",
        help_text="Set when classroom is null — student practicing on own.",
    )
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assignments",
        help_text="If unset, this is a teacher-authored custom assignment with its own testcases.",
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    language = models.CharField(max_length=12, choices=Language.choices, default=Language.PYTHON)
    level = models.CharField(max_length=10, blank=True, default="")
    starter_code = models.TextField(blank=True)
    max_points = models.PositiveIntegerField(default=100)

    # Window — either a hard deadline or a per-attempt timer. Both can co-exist.
    start_at = models.DateTimeField(null=True, blank=True)
    due_at = models.DateTimeField(null=True, blank=True)
    time_limit_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="If set, each student gets this many minutes from first start.",
    )

    strict_mode = models.BooleanField(
        default=True,
        help_text="Fullscreen lock + paste/copy/contextmenu/devtools blockers active.",
    )
    max_attempts = models.PositiveSmallIntegerField(default=0, help_text="0 = unlimited")
    is_published = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        owner = self.classroom.name if self.classroom_id else "Solo"
        return f"{owner} — {self.title}"

    # ----- accessors -----
    def get_test_cases(self):
        if self.exercise_id:
            return self.exercise.test_cases.all()
        return self.custom_test_cases.all()

    def visible_test_cases(self):
        return self.get_test_cases().filter(is_hidden=False)

    def is_open(self) -> bool:
        now = timezone.now()
        if self.start_at and now < self.start_at:
            return False
        if self.due_at and now > self.due_at:
            return False
        return self.is_published

    @property
    def is_solo(self) -> bool:
        return self.classroom_id is None and self.solo_owner_id is not None

    def viewable_by(self, user) -> bool:
        if self.is_solo:
            return self.solo_owner_id == user.id
        if self.classroom_id is None:
            return False
        from apps.classrooms.models import Membership
        if self.classroom.teacher_id == user.id:
            return True
        return Membership.objects.filter(classroom_id=self.classroom_id, student=user).exists()


class AttemptStatus(models.TextChoices):
    ACTIVE      = "active",     "Active"
    SUBMITTED   = "submitted",  "Submitted"
    EXPIRED     = "expired",    "Expired"
    TERMINATED  = "terminated", "Terminated"


class AssignmentAttempt(models.Model):
    """Server-authoritative session: gates time limits, scopes cheat events."""

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="attempts")
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=AttemptStatus.choices, default=AttemptStatus.ACTIVE)

    # Live counters refreshed via realtime events
    cheat_event_count = models.PositiveIntegerField(default=0)
    submission_count = models.PositiveIntegerField(default=0)

    # Final grade snapshot (denormalized for leaderboard speed)
    best_score = models.PositiveIntegerField(default=0)
    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ("-started_at",)
        indexes = [
            models.Index(fields=("assignment", "student")),
            models.Index(fields=("status",)),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=("assignment", "student"),
                condition=models.Q(status=AttemptStatus.ACTIVE),
                name="unique_active_attempt_per_student",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.student} → {self.assignment} [{self.status}]"

    def deadline(self):
        """Effective end time given assignment's time_limit + due_at."""
        candidates = []
        if self.assignment.time_limit_minutes:
            from datetime import timedelta
            candidates.append(self.started_at + timedelta(minutes=self.assignment.time_limit_minutes))
        if self.assignment.due_at:
            candidates.append(self.assignment.due_at)
        if not candidates:
            return None
        return min(candidates)

    def is_expired(self) -> bool:
        d = self.deadline()
        return bool(d and timezone.now() > d)

    def remaining_seconds(self) -> int | None:
        d = self.deadline()
        if not d:
            return None
        delta = (d - timezone.now()).total_seconds()
        return max(0, int(delta))


def _validate_test_case_owner(testcase):
    """Custom testcases must point to either an exercise or an assignment, never both."""
    if bool(testcase.exercise_id) == bool(testcase.assignment_id):
        raise ValidationError("TestCase must belong to exactly one of {exercise, assignment}.")


class AssignmentMetrics(models.Model):
    """Aggregated metrics — recomputed by `aggregate_assignment_metrics` task."""

    assignment = models.OneToOneField(
        Assignment,
        on_delete=models.CASCADE,
        related_name="metrics",
    )
    students_started = models.PositiveIntegerField(default=0)
    students_completed = models.PositiveIntegerField(default=0)
    completion_rate = models.FloatField(default=0)
    median_solve_seconds = models.PositiveIntegerField(default=0)
    avg_runs = models.FloatField(default=0)
    hint_usage_pct = models.FloatField(default=0)
    most_failed_test = models.ForeignKey(
        "exercises.TestCase",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    common_errors = models.JSONField(
        default=list,
        blank=True,
        help_text="[{label,count}] sorted desc — exception types, failed testcase names, stderr fingerprints.",
    )
    computed_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"metrics[{self.assignment_id}]"
