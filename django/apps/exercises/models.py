"""Exercise library — pre-baked tasks teachers can pick from.

A teacher can create a Custom assignment (no exercise FK), or attach
an Exercise. TestCase rows belong to the Exercise; for custom
assignments they belong to the Assignment instead (see assignments.models).
"""
from __future__ import annotations

from django.conf import settings
from django.db import models


class Language(models.TextChoices):
    PYTHON = "python", "Python"
    WEB = "web",       "HTML / CSS / JS"


class Level(models.TextChoices):
    EASY   = "easy",   "Easy"
    MEDIUM = "medium", "Medium"
    HARD   = "hard",   "Hard"


LEVEL_XP = {
    Level.EASY: 50,
    Level.MEDIUM: 120,
    Level.HARD: 250,
}


class Concept(models.Model):
    """Pedagogical tag — exercises map to concepts; mastery tracked per student."""

    slug = models.SlugField(unique=True, max_length=64)
    name = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class Exercise(models.Model):
    slug = models.SlugField(unique=True, max_length=80)
    title = models.CharField(max_length=160)
    language = models.CharField(max_length=12, choices=Language.choices)
    level = models.CharField(max_length=10, choices=Level.choices)

    prompt_md = models.TextField(help_text="Problem statement, markdown allowed")
    starter_code = models.TextField(blank=True)
    reference_solution = models.TextField(blank=True)
    hints = models.JSONField(default=list, blank=True)

    tags = models.JSONField(default=list, blank=True)
    concepts = models.ManyToManyField(
        Concept,
        blank=True,
        related_name="exercises",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("language", "level", "title")
        indexes = [models.Index(fields=("language", "level"))]

    def __str__(self) -> str:
        return f"[{self.language}/{self.level}] {self.title}"

    @property
    def base_xp(self) -> int:
        return LEVEL_XP.get(self.level, 50)


class TestCase(models.Model):
    """One stdin/stdout case (python) OR one assertion (web)."""

    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name="test_cases",
        null=True,
        blank=True,
    )
    # If this testcase belongs to a teacher's CUSTOM assignment instead
    # of a library exercise, point to the Assignment via this FK.
    assignment = models.ForeignKey(
        "assignments.Assignment",
        on_delete=models.CASCADE,
        related_name="custom_test_cases",
        null=True,
        blank=True,
    )

    name = models.CharField(max_length=120)

    # Python / stdin-stdout style
    stdin = models.TextField(blank=True)
    expected_stdout = models.TextField(blank=True)

    # Web-style — list of assertions to run inside the iframe sandbox.
    # Shape: [{"id":"a1","desc":"Has h1","kind":"selector","selector":"h1"}, ...]
    assertions = models.JSONField(default=list, blank=True)

    is_hidden = models.BooleanField(
        default=False,
        help_text="Hidden cases run during grading but aren't shown to students.",
    )
    weight = models.PositiveSmallIntegerField(default=1)
    ordering = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("ordering", "id")

    def __str__(self) -> str:
        return self.name


class Hint(models.Model):
    """Teacher-authored progressive hint, revealed by student at XP cost."""

    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name="structured_hints",
    )
    level = models.PositiveSmallIntegerField(default=1, help_text="1 = first hint shown.")
    content = models.TextField()
    penalty = models.PositiveSmallIntegerField(
        default=0,
        help_text="XP deducted from the eventual submission grade if revealed.",
    )

    class Meta:
        ordering = ("exercise", "level")
        unique_together = (("exercise", "level"),)

    def __str__(self) -> str:
        return f"{self.exercise.slug}·hint{self.level}"


class HintReveal(models.Model):
    """A student exposing a hint during an attempt — applies penalty at grade time."""

    attempt = models.ForeignKey(
        "assignments.AssignmentAttempt",
        on_delete=models.CASCADE,
        related_name="hint_reveals",
    )
    hint = models.ForeignKey(Hint, on_delete=models.CASCADE, related_name="reveals")
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hint_reveals",
    )
    revealed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("attempt", "hint"),)
        ordering = ("attempt", "revealed_at")
        indexes = [models.Index(fields=("attempt",))]


class ConceptMastery(models.Model):
    """Per-student mastery score per concept — bumped on testcase passes."""

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="concept_mastery",
    )
    concept = models.ForeignKey(
        Concept,
        on_delete=models.CASCADE,
        related_name="mastery_records",
    )
    score = models.FloatField(default=0, help_text="0..1; EMA over passed/total ratio.")
    attempts = models.PositiveIntegerField(default=0)
    last_activity = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = (("student", "concept"),)
        ordering = ("-score",)
        indexes = [models.Index(fields=("student",)), models.Index(fields=("concept",))]

    def __str__(self) -> str:
        return f"{self.student_id}·{self.concept.slug}={self.score:.2f}"
