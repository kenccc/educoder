from __future__ import annotations

import secrets

from django.conf import settings
from django.db import models


def _join_code() -> str:
    return secrets.token_urlsafe(6).upper().replace("_", "").replace("-", "")[:8]


class Classroom(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="taught_classrooms",
    )
    join_code = models.CharField(max_length=12, unique=True, default=_join_code)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.name


class Membership(models.Model):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name="memberships")
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="classroom_memberships",
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("classroom", "student")
