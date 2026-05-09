"""Custom user model with role split (student/teacher/admin)."""
from __future__ import annotations

from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    STUDENT = "student", "Student"
    TEACHER = "teacher", "Teacher"
    ADMIN = "admin", "Admin"


class User(AbstractUser):
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.STUDENT)
    display_name = models.CharField(max_length=120, blank=True)

    @property
    def is_teacher(self) -> bool:
        return self.role in (Role.TEACHER, Role.ADMIN)

    @property
    def is_student(self) -> bool:
        return self.role == Role.STUDENT
