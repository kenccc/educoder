from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Exists, Max, OuterRef, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from apps.submissions.models import Submission
from services.classrooms import ClassroomService

from .models import Classroom, Membership

User = get_user_model()


@login_required
def classroom_list(request):
    rows = ClassroomService.list_for_user(request.user)
    return render(request, "classrooms/list.html", {"classrooms": rows})


@login_required
def classroom_detail(request, pk: int):
    classroom = get_object_or_404(Classroom, pk=pk)
    ClassroomService.assert_member_or_teacher(classroom, request.user)
    members = ClassroomService.members(classroom)
    is_owner = classroom.teacher_id == request.user.id

    base_qs = classroom.assignments.select_related("exercise")
    if is_owner:
        # Teacher: how many distinct students have a correct submission per task.
        assignments = base_qs.annotate(
            completed_count=Count(
                "submissions__student",
                filter=Q(submissions__is_correct=True),
                distinct=True,
            ),
        ).order_by("-created_at")
    else:
        # Student: did THIS student ever pass.
        assignments = base_qs.annotate(
            is_done=Exists(
                Submission.objects.filter(
                    assignment_id=OuterRef("pk"),
                    student=request.user,
                    is_correct=True,
                )
            ),
        ).order_by("-created_at")

    return render(
        request,
        "classrooms/detail.html",
        {
            "classroom": classroom,
            "members": members,
            "assignments": assignments,
            "is_owner": is_owner,
            "roster_count": len(members),
        },
    )


@login_required
def student_detail(request, pk: int, student_id: int):
    """Teacher view: one student's activity in this classroom."""
    from apps.assignments.models import Assignment, AssignmentAttempt
    from apps.exercises.models import ConceptMastery, HintReveal
    from apps.realtime.models import (
        CheatEvent,
        ClassroomEvent,
        CodeSnapshot,
        StudentStatus,
    )

    classroom = get_object_or_404(Classroom, pk=pk)
    if classroom.teacher_id != request.user.id:
        raise PermissionDenied()

    student = get_object_or_404(User, pk=student_id)
    # Confirm student is in this classroom.
    if not Membership.objects.filter(classroom=classroom, student=student).exists():
        raise PermissionDenied("Not a member of this classroom.")

    assignments = list(
        Assignment.objects.filter(classroom=classroom).order_by("-created_at")
    )

    # Best attempt per assignment for this student.
    attempts = (
        AssignmentAttempt.objects
        .filter(student=student, assignment__classroom=classroom)
        .order_by("assignment_id", "-is_correct", "-best_score", "-started_at")
    )
    best_by_assign: dict[int, AssignmentAttempt] = {}
    for a in attempts:
        if a.assignment_id not in best_by_assign:
            best_by_assign[a.assignment_id] = a

    # Submission stats per assignment.
    sub_stats = (
        Submission.objects
        .filter(student=student, assignment__classroom=classroom)
        .values("assignment_id")
        .annotate(runs=Count("id"), last=Max("created_at"))
    )
    sub_by_assign = {row["assignment_id"]: row for row in sub_stats}

    # Hints used per assignment.
    hint_stats = (
        HintReveal.objects.filter(
            student=student, attempt__assignment__classroom=classroom
        )
        .values("attempt__assignment_id")
        .annotate(n=Count("id"))
    )
    hints_by_assign = {row["attempt__assignment_id"]: row["n"] for row in hint_stats}

    rows = []
    done = working = 0
    for a in assignments:
        att = best_by_assign.get(a.id)
        if att and att.is_correct:
            state = "done"
            done += 1
        elif att:
            state = "working"
            working += 1
        else:
            state = "not_started"
        sub = sub_by_assign.get(a.id, {})
        rows.append({
            "assignment": a,
            "state": state,
            "attempt": att,
            "best_score": att.best_score if att else 0,
            "runs": sub.get("runs") or 0,
            "last": sub.get("last"),
            "hints_used": hints_by_assign.get(a.id, 0),
        })

    total_runs = sum(r["runs"] for r in rows)
    total_hints = sum(r["hints_used"] for r in rows)
    cheat_count = CheatEvent.objects.filter(
        student=student, attempt__assignment__classroom=classroom
    ).count()

    # Recent activity feed (last 80 events).
    recent_events = list(
        ClassroomEvent.objects
        .filter(user=student, classroom=classroom)
        .select_related("assignment")
        .order_by("-created_at")[:80]
    )

    # Recent code snapshots across all attempts in this classroom (last 12).
    recent_snaps = list(
        CodeSnapshot.objects
        .filter(attempt__student=student, attempt__assignment__classroom=classroom)
        .select_related("attempt", "attempt__assignment")
        .order_by("-created_at")[:12]
    )

    mastery = list(
        ConceptMastery.objects
        .filter(student=student)
        .select_related("concept")
        .order_by("-score")[:12]
    )

    status = StudentStatus.objects.filter(student=student).first()

    return render(
        request,
        "classrooms/student_detail.html",
        {
            "classroom": classroom,
            "student": student,
            "rows": rows,
            "summary": {
                "total": len(assignments),
                "done": done,
                "working": working,
                "not_started": len(assignments) - done - working,
                "runs": total_runs,
                "hints": total_hints,
                "cheats": cheat_count,
            },
            "recent_events": recent_events,
            "recent_snaps": recent_snaps,
            "mastery": mastery,
            "status": status,
        },
    )


@login_required
@require_http_methods(["POST"])
def classroom_create(request):
    try:
        classroom = ClassroomService.create(
            teacher=request.user,
            name=request.POST.get("name", "").strip(),
            description=request.POST.get("description", "").strip(),
        )
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("classrooms:list")
    messages.success(request, f"Classroom '{classroom.name}' created.")
    return redirect("classrooms:detail", pk=classroom.pk)


@login_required
@require_http_methods(["POST"])
def classroom_join(request):
    try:
        classroom = ClassroomService.join(
            student=request.user,
            join_code=request.POST.get("join_code", ""),
        )
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("classrooms:list")
    messages.success(request, f"Joined {classroom.name}.")
    return redirect("classrooms:detail", pk=classroom.pk)
