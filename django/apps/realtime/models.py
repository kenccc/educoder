from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.assignments.models import Assignment, AssignmentAttempt
from apps.classrooms.models import Classroom


class CheatKind(models.TextChoices):
    PASTE         = "paste",         "Paste"
    COPY          = "copy",          "Copy"
    CUT           = "cut",           "Cut"
    CONTEXTMENU   = "contextmenu",   "Right-click menu"
    KEY_COMBO     = "key_combo",     "Forbidden key combo"
    DEVTOOLS      = "devtools",      "DevTools opened"
    DOM_TAMPER    = "dom_tamper",    "DOM tampered"
    FULLSCREEN    = "fullscreen",    "Left fullscreen"
    TAB_BLUR      = "tab_blur",      "Tab/window blurred"
    VISIBILITY    = "visibility",    "Page hidden"
    NETWORK_OPEN  = "network_open",  "Window opened"
    SUSPECT       = "suspect",       "Suspicious activity"


class CheatEvent(models.Model):
    attempt = models.ForeignKey(
        AssignmentAttempt,
        on_delete=models.CASCADE,
        related_name="cheat_events",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cheat_events",
    )
    kind = models.CharField(max_length=20, choices=CheatKind.choices)
    payload = models.JSONField(default=dict, blank=True)
    severity = models.PositiveSmallIntegerField(default=1)
    occurred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-occurred_at",)
        indexes = [
            models.Index(fields=("attempt",)),
            models.Index(fields=("kind",)),
        ]

    def __str__(self) -> str:
        return f"{self.student} · {self.kind} @ {self.occurred_at:%H:%M:%S}"


class EventType(models.TextChoices):
    # Editor / activity
    EDITOR_SNAPSHOT  = "editor_snapshot",  "Editor snapshot"
    RUN_CODE         = "run_code",         "Run code"
    SUBMISSION       = "submission",       "Submission"
    TESTCASE_PASS    = "testcase_pass",    "Test case passed"
    TESTCASE_FAIL    = "testcase_fail",    "Test case failed"
    # Hints
    HINT_OPEN        = "hint_open",        "Hint opened"
    # Anti-cheat (mirror of CheatKind)
    PASTE            = "paste",            "Paste"
    COPY             = "copy",             "Copy"
    BLUR             = "blur",             "Tab/window blur"
    FOCUS            = "focus",            "Tab/window focus"
    FULLSCREEN_EXIT  = "fullscreen_exit",  "Left fullscreen"
    DEVTOOLS         = "devtools",         "DevTools opened"
    DOM_TAMPER       = "dom_tamper",       "DOM tampered"
    KEY_COMBO        = "key_combo",        "Forbidden key combo"
    CONTEXTMENU      = "contextmenu",      "Right-click menu"
    NETWORK_OPEN     = "network_open",     "Window opened"
    VISIBILITY       = "visibility",       "Page hidden"
    SUSPECT          = "suspect",          "Suspicious activity"
    # Lifecycle
    ATTEMPT_START    = "attempt_start",    "Attempt started"
    ATTEMPT_END      = "attempt_end",      "Attempt ended"
    PRESENCE_ONLINE  = "presence_online",  "Presence online"
    PRESENCE_OFFLINE = "presence_offline", "Presence offline"
    # Status engine
    STATUS_CHANGE    = "status_change",    "Status change"


# Event types broadcast to teacher dashboard. The rest are DB-only
# (high-volume signals that would drown the live feed).
BROADCAST_EVENT_TYPES = frozenset({
    EventType.RUN_CODE,
    EventType.SUBMISSION,
    EventType.TESTCASE_PASS,
    EventType.TESTCASE_FAIL,
    EventType.HINT_OPEN,
    EventType.STATUS_CHANGE,
    EventType.ATTEMPT_START,
    EventType.ATTEMPT_END,
    EventType.PRESENCE_ONLINE,
    EventType.PRESENCE_OFFLINE,
    # Cheat-style events the teacher cares about live
    EventType.PASTE,
    EventType.DEVTOOLS,
    EventType.FULLSCREEN_EXIT,
    EventType.NETWORK_OPEN,
    EventType.SUSPECT,
})


class ClassroomEvent(models.Model):
    """Append-only event stream — feeds dashboards, timeline replay, analytics."""

    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.CASCADE,
        related_name="events",
        null=True,
        blank=True,
        help_text="Null for solo-practice events.",
    )
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name="events",
        null=True,
        blank=True,
    )
    attempt = models.ForeignKey(
        AssignmentAttempt,
        on_delete=models.CASCADE,
        related_name="events",
        null=True,
        blank=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="classroom_events",
    )
    type = models.CharField(max_length=32, choices=EventType.choices)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("classroom", "-created_at")),
            models.Index(fields=("user", "-created_at")),
            models.Index(fields=("assignment", "-created_at")),
            models.Index(fields=("attempt", "-created_at")),
            models.Index(fields=("type",)),
        ]

    def __str__(self) -> str:
        return f"{self.user_id}·{self.type}@{self.created_at:%H:%M:%S}"


class SnapshotTrigger(models.TextChoices):
    RUN      = "run",      "Run"
    SUBMIT   = "submit",   "Submit"
    DEBOUNCE = "debounce", "Debounce"


class CodeSnapshot(models.Model):
    """Code-state snapshot taken on run, submit, and 30s debounce while editing."""

    attempt = models.ForeignKey(
        AssignmentAttempt,
        on_delete=models.CASCADE,
        related_name="snapshots",
    )
    code = models.TextField()
    trigger = models.CharField(max_length=10, choices=SnapshotTrigger.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("attempt", "-created_at")),
        ]

    def __str__(self) -> str:
        return f"snap[{self.attempt_id}]·{self.trigger}@{self.created_at:%H:%M:%S}"


class StudentStatusKind(models.TextChoices):
    OFFLINE      = "offline",      "Offline"
    IDLE         = "idle",         "Idle"
    ONLINE       = "online",       "Online"
    PROGRESSING  = "progressing",  "Progressing"
    STRUGGLING   = "struggling",   "Struggling"
    STUCK        = "stuck",        "Stuck"


class StudentStatus(models.Model):
    """Denormalized realtime state — refreshed by `compute_student_status` task."""

    student = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="status",
    )
    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="active_statuses",
    )
    active_assignment = models.ForeignKey(
        Assignment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    active_attempt = models.ForeignKey(
        AssignmentAttempt,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    status = models.CharField(
        max_length=16,
        choices=StudentStatusKind.choices,
        default=StudentStatusKind.OFFLINE,
    )
    stuck_score = models.FloatField(default=0)
    last_activity = models.DateTimeField(null=True, blank=True)
    last_run_at = models.DateTimeField(null=True, blank=True)
    last_pass_at = models.DateTimeField(null=True, blank=True)
    progress = models.FloatField(default=0, help_text="0..1 fraction of testcases passed.")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=("classroom", "status")),
            models.Index(fields=("status",)),
        ]

    def __str__(self) -> str:
        return f"{self.student_id}·{self.status}"
