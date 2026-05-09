from __future__ import annotations

from django.core.exceptions import PermissionDenied
from django.db.models import Q

from apps.classrooms.models import Classroom, Membership


class ClassroomService:
    @staticmethod
    def list_for_user(user) -> list[Classroom]:
        return list(
            Classroom.objects.filter(
                Q(teacher=user) | Q(memberships__student=user)
            )
            .filter(is_archived=False)
            .distinct()
            .select_related("teacher")
        )

    @staticmethod
    def create(*, teacher, name: str, description: str = "") -> Classroom:
        if not teacher.is_authenticated:
            raise PermissionDenied("Login required")
        if not getattr(teacher, "is_teacher", False):
            raise PermissionDenied("Only teachers can create classrooms")
        if not name:
            raise ValueError("Classroom name is required")
        return Classroom.objects.create(teacher=teacher, name=name, description=description)

    @staticmethod
    def join(*, student, join_code: str) -> Classroom:
        code = (join_code or "").strip().upper()
        if not code:
            raise ValueError("join_code required")
        try:
            classroom = Classroom.objects.get(join_code=code, is_archived=False)
        except Classroom.DoesNotExist as exc:
            raise ValueError("invalid join code") from exc
        Membership.objects.get_or_create(classroom=classroom, student=student)
        return classroom

    @staticmethod
    def assert_teacher(classroom: Classroom, user) -> None:
        if classroom.teacher_id != user.id:
            raise PermissionDenied("Only the owning teacher can do that")

    @staticmethod
    def assert_member_or_teacher(classroom: Classroom, user) -> None:
        if classroom.teacher_id == user.id:
            return
        if Membership.objects.filter(classroom=classroom, student=user).exists():
            return
        raise PermissionDenied("Not a member of this classroom")

    @staticmethod
    def members(classroom: Classroom):
        return (
            Membership.objects
            .filter(classroom=classroom)
            .select_related("student")
            .order_by("student__username")
        )
