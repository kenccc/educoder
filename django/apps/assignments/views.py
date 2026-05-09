from __future__ import annotations

import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Count, Max, Q
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from apps.classrooms.models import Classroom
from apps.exercises.models import Exercise, Language, Level, TestCase
from apps.realtime.models import CheatEvent
from apps.submissions.models import Submission
from services.classrooms import ClassroomService
from services.gamification import LeaderboardService
from services.submissions import AttemptService, SubmissionService, is_web

from .models import Assignment, AssignmentAttempt, AttemptStatus


@login_required
def assignment_detail(request, pk: int):
    assignment = get_object_or_404(
        Assignment.objects.select_related("classroom", "exercise"), pk=pk
    )
    if not assignment.viewable_by(request.user):
        raise PermissionDenied()

    is_owner = (
        assignment.classroom_id is not None
        and assignment.classroom.teacher_id == request.user.id
    )

    submissions = (
        Submission.objects
        .filter(assignment=assignment, student=request.user)
        .order_by("-created_at")[:20]
    )

    visible_cases = list(assignment.visible_test_cases())

    return render(
        request,
        "assignments/detail.html",
        {
            "assignment": assignment,
            "is_owner": is_owner,
            "submissions": submissions,
            "visible_cases": visible_cases,
            "now": timezone.now(),
        },
    )


@login_required
def assignment_new(request, classroom_id: int):
    """Teacher: create-assignment form (pick exercise OR custom)."""
    classroom = get_object_or_404(Classroom, pk=classroom_id)
    ClassroomService.assert_teacher(classroom, request.user)

    language = request.GET.get("language", "")
    level = request.GET.get("level", "")
    q = (request.GET.get("q") or "").strip()
    qs = Exercise.objects.all()
    if language in Language.values:
        qs = qs.filter(language=language)
    if level in Level.values:
        qs = qs.filter(level=level)
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(slug__icontains=q))
    qs = qs.order_by("language", "level", "title")

    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get("page"))

    params = request.GET.copy()
    params.pop("page", None)
    qs_no_page = params.urlencode()

    return render(
        request,
        "assignments/new.html",
        {
            "classroom": classroom,
            "page_obj": page,
            "exercises": page.object_list,
            "total": paginator.count,
            "languages": Language.choices,
            "levels": Level.choices,
            "selected_language": language,
            "selected_level": level,
            "q": q,
            "qs_no_page": qs_no_page,
        },
    )


@login_required
@require_POST
def assignment_create_from_exercise(request, classroom_id: int):
    classroom = get_object_or_404(Classroom, pk=classroom_id)
    ClassroomService.assert_teacher(classroom, request.user)
    exercise = get_object_or_404(Exercise, pk=request.POST.get("exercise_id"))

    a = Assignment.objects.create(
        classroom=classroom,
        exercise=exercise,
        title=request.POST.get("title") or exercise.title,
        description=request.POST.get("description") or exercise.prompt_md,
        language=exercise.language,
        level=exercise.level,
        starter_code=exercise.starter_code,
        time_limit_minutes=_int_or_none(request.POST.get("time_limit_minutes")),
        due_at=_dt_or_none(request.POST.get("due_at")),
        strict_mode=request.POST.get("strict_mode") == "on",
        is_published=True,
    )
    messages.success(request, f"Assigned: {a.title}")
    return redirect("classrooms:detail", pk=classroom.pk)


@login_required
@require_POST
def assignment_create_custom(request, classroom_id: int):
    classroom = get_object_or_404(Classroom, pk=classroom_id)
    ClassroomService.assert_teacher(classroom, request.user)

    a = Assignment.objects.create(
        classroom=classroom,
        title=request.POST.get("title") or "Untitled",
        description=request.POST.get("description") or "",
        language=request.POST.get("language") or Language.PYTHON,
        level=request.POST.get("level") or "",
        starter_code=request.POST.get("starter_code") or "",
        time_limit_minutes=_int_or_none(request.POST.get("time_limit_minutes")),
        due_at=_dt_or_none(request.POST.get("due_at")),
        strict_mode=request.POST.get("strict_mode") == "on",
        is_published=True,
    )

    raw = request.POST.get("test_cases_json") or "[]"
    try:
        cases = json.loads(raw)
    except ValueError:
        cases = []
    for i, c in enumerate(cases):
        TestCase.objects.create(
            assignment=a,
            name=c.get("name") or f"Case {i+1}",
            stdin=c.get("stdin", ""),
            expected_stdout=c.get("expected_stdout", ""),
            assertions=c.get("assertions", []),
            is_hidden=bool(c.get("is_hidden")),
            ordering=i,
        )
    messages.success(request, f"Custom assignment '{a.title}' created.")
    return redirect("classrooms:detail", pk=classroom.pk)


@login_required
def attempt_start(request, assignment_id: int):
    """Begin/resume an attempt — redirects to the IDE."""
    assignment = get_object_or_404(
        Assignment.objects.select_related("classroom", "exercise"), pk=assignment_id
    )
    if not assignment.viewable_by(request.user):
        raise PermissionDenied()
    if assignment.classroom_id and assignment.classroom.teacher_id == request.user.id:
        messages.info(request, "Teachers can preview, but XP is awarded only to students.")
    try:
        attempt = AttemptService.get_or_create(assignment=assignment, student=request.user)
    except (ValidationError, PermissionDenied) as exc:
        messages.error(request, str(exc))
        return redirect("assignments:detail", pk=assignment.pk)
    return redirect("assignments:attempt", attempt_id=attempt.pk)


@login_required
def attempt_ide(request, attempt_id: int):
    attempt = get_object_or_404(
        AssignmentAttempt.objects.select_related(
            "assignment", "assignment__classroom", "assignment__exercise", "student"
        ),
        pk=attempt_id,
    )
    a = attempt.assignment
    is_teacher_of_room = (
        a.classroom_id is not None and a.classroom.teacher_id == request.user.id
    )
    if attempt.student_id != request.user.id and not is_teacher_of_room:
        raise PermissionDenied()

    all_cases = list(attempt.assignment.get_test_cases())
    visible_cases = [c for c in all_cases if not c.is_hidden]
    # Web grading runs in the browser, so we cannot meaningfully hide assertions
    # from the student. Only ship visible cases — hidden web cases simply skip.
    web_cases = [
        {"name": c.name, "is_hidden": False, "assertions": c.assertions}
        for c in visible_cases
    ]

    from apps.exercises.models import Hint, HintReveal
    hints = []
    revealed_hint_ids: set[int] = set()
    if attempt.assignment.exercise_id:
        hints = list(
            Hint.objects.filter(exercise_id=attempt.assignment.exercise_id).order_by("level")
        )
        revealed_hint_ids = set(
            HintReveal.objects.filter(attempt=attempt).values_list("hint_id", flat=True)
        )

    return render(
        request,
        "assignments/attempt.html",
        {
            "attempt": attempt,
            "assignment": attempt.assignment,
            "visible_cases": visible_cases,
            "remaining_seconds": attempt.remaining_seconds(),
            "is_web": attempt.assignment.language == Language.WEB,
            "web_cases_json": web_cases,
            "hints": hints,
            "revealed_hint_ids": list(revealed_hint_ids),
        },
    )


@login_required
@require_POST
def attempt_snapshot(request, attempt_id: int):
    """Capture a code snapshot — debounced 30s + on run/submit. Records editor_snapshot event."""
    attempt = get_object_or_404(
        AssignmentAttempt.objects.select_related("assignment", "assignment__classroom"),
        pk=attempt_id,
    )
    if attempt.student_id != request.user.id:
        raise PermissionDenied()
    if attempt.status != AttemptStatus.ACTIVE:
        return JsonResponse({"ok": False, "reason": "inactive"}, status=409)

    try:
        body = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return HttpResponseBadRequest("invalid json")

    code = (body.get("code") or "")
    trigger = (body.get("trigger") or "debounce")[:10]

    from apps.realtime.models import CodeSnapshot, EventType, SnapshotTrigger
    from services.events import EventService
    if trigger not in {t.value for t in SnapshotTrigger}:
        trigger = SnapshotTrigger.DEBOUNCE.value

    # Idempotency: skip if last snapshot has the same code (debounce churn).
    last = (
        CodeSnapshot.objects.filter(attempt=attempt)
        .only("code", "id")
        .order_by("-created_at")
        .first()
    )
    if last is None or last.code != code:
        CodeSnapshot.objects.create(attempt=attempt, code=code, trigger=trigger)

    EventService.record(
        user=request.user,
        assignment=attempt.assignment,
        attempt=attempt,
        type=EventType.EDITOR_SNAPSHOT.value,
        payload={"trigger": trigger, "code_len": len(code)},
    )
    return JsonResponse({"ok": True})


@login_required
def assignment_students(request, assignment_id: int):
    """Teacher view: per-assignment student roster — completion + score + attempt links."""
    from apps.classrooms.models import Membership
    from apps.exercises.models import HintReveal

    assignment = get_object_or_404(
        Assignment.objects.select_related("classroom", "exercise"),
        pk=assignment_id,
    )
    if not (assignment.classroom_id and assignment.classroom.teacher_id == request.user.id):
        raise PermissionDenied()

    members = list(
        Membership.objects.filter(classroom=assignment.classroom)
        .select_related("student")
        .order_by("student__username")
    )

    # Best attempt per student (preferring is_correct, then highest best_score, latest started).
    attempts = (
        AssignmentAttempt.objects
        .filter(assignment=assignment)
        .select_related("student")
        .order_by("student_id", "-is_correct", "-best_score", "-started_at")
    )
    best_by_student: dict[int, AssignmentAttempt] = {}
    for a in attempts:
        if a.student_id not in best_by_student:
            best_by_student[a.student_id] = a

    # Submission counts + last activity per student.
    sub_stats = (
        Submission.objects
        .filter(assignment=assignment)
        .values("student_id")
        .annotate(runs=Count("id"), last=Max("created_at"))
    )
    sub_by_student = {row["student_id"]: row for row in sub_stats}

    # Hints used per student.
    hint_counts = (
        HintReveal.objects
        .filter(attempt__assignment=assignment)
        .values("student_id")
        .annotate(n=Count("id"))
    )
    hints_by_student = {row["student_id"]: row["n"] for row in hint_counts}

    rows = []
    completed = 0
    in_progress = 0
    for m in members:
        a = best_by_student.get(m.student_id)
        sub = sub_by_student.get(m.student_id, {})
        if a and a.is_correct:
            state = "done"
            completed += 1
        elif a:
            state = "working"
            in_progress += 1
        else:
            state = "not_started"
        rows.append({
            "student": m.student,
            "state": state,
            "best_score": a.best_score if a else 0,
            "best_attempt": a,
            "runs": sub.get("runs") or 0,
            "last_activity": sub.get("last"),
            "hints_used": hints_by_student.get(m.student_id, 0),
        })

    return render(
        request,
        "assignments/students.html",
        {
            "assignment": assignment,
            "rows": rows,
            "stats": {
                "total": len(members),
                "done": completed,
                "working": in_progress,
                "not_started": len(members) - completed - in_progress,
            },
        },
    )


@login_required
def classroom_leaderboard(request, classroom_id: int):
    classroom = get_object_or_404(Classroom, pk=classroom_id)
    ClassroomService.assert_member_or_teacher(classroom, request.user)
    rows = LeaderboardService.for_classroom(classroom)
    return render(
        request,
        "assignments/leaderboard.html",
        {"classroom": classroom, "rows": rows},
    )


def _build_timeline_context(attempt):
    """Shared data assembly for full and partial timeline renders."""
    from apps.realtime.models import ClassroomEvent, CodeSnapshot

    a = attempt.assignment
    events = list(
        ClassroomEvent.objects
        .filter(attempt=attempt)
        .select_related("user")
        .order_by("created_at")
    )
    snapshots = list(
        CodeSnapshot.objects.filter(attempt=attempt).order_by("created_at")
    )
    cheats = list(
        CheatEvent.objects.filter(attempt=attempt).order_by("occurred_at")
    )
    submissions = list(
        Submission.objects.filter(attempt=attempt).order_by("created_at")
    )

    enriched_snaps = []
    prev_code = ""
    for s in snapshots:
        added = max(0, len(s.code.splitlines()) - len(prev_code.splitlines()))
        removed = max(0, len(prev_code.splitlines()) - len(s.code.splitlines()))
        enriched_snaps.append({
            "id": s.id,
            "code": s.code,
            "trigger": s.trigger,
            "created_at": s.created_at,
            "added_lines": added,
            "removed_lines": removed,
            "lines": len(s.code.splitlines()),
            "prev_code": prev_code,
        })
        prev_code = s.code

    return {
        "attempt": attempt,
        "assignment": a,
        "events": events,
        "snapshots": enriched_snaps,
        "cheats": cheats,
        "submissions": submissions,
    }


def _check_timeline_permission(attempt, user):
    a = attempt.assignment
    is_room_teacher = a.classroom_id is not None and a.classroom.teacher_id == user.id
    return is_room_teacher or attempt.student_id == user.id


@login_required
def attempt_timeline(request, attempt_id: int):
    """Teacher view: chronological events + code snapshots for a single attempt."""
    attempt = get_object_or_404(
        AssignmentAttempt.objects.select_related(
            "assignment", "assignment__classroom", "student"
        ),
        pk=attempt_id,
    )
    if not _check_timeline_permission(attempt, request.user):
        raise PermissionDenied()

    ctx = _build_timeline_context(attempt)

    if request.headers.get("HX-Request"):
        return render(request, "assignments/timeline_body.html", ctx)

    return render(request, "assignments/timeline.html", ctx)


@login_required
def assignment_analytics(request, assignment_id: int):
    """Teacher view: per-assignment metrics + common errors + concept breakdown."""
    from apps.assignments.models import AssignmentMetrics
    from apps.exercises.models import ConceptMastery

    assignment = get_object_or_404(
        Assignment.objects.select_related("classroom", "exercise"),
        pk=assignment_id,
    )
    if not (assignment.classroom_id and assignment.classroom.teacher_id == request.user.id):
        raise PermissionDenied()

    metrics = AssignmentMetrics.objects.filter(assignment=assignment).select_related(
        "most_failed_test"
    ).first()

    # Concept breakdown: avg mastery per concept across the classroom roster.
    concept_rows: list[dict] = []
    if assignment.exercise_id:
        concepts = list(assignment.exercise.concepts.all())
        if concepts and assignment.classroom_id:
            from apps.classrooms.models import Membership
            student_ids = list(
                Membership.objects
                .filter(classroom=assignment.classroom)
                .values_list("student_id", flat=True)
            )
            for c in concepts:
                rec = (
                    ConceptMastery.objects
                    .filter(concept=c, student_id__in=student_ids)
                    .values_list("score", flat=True)
                )
                rec = list(rec)
                avg = (sum(rec) / len(rec)) if rec else 0.0
                concept_rows.append({"concept": c, "avg": avg, "n": len(rec)})

    return render(
        request,
        "assignments/analytics.html",
        {
            "assignment": assignment,
            "metrics": metrics,
            "concept_rows": concept_rows,
        },
    )


@login_required
def classroom_monitor(request, classroom_id: int):
    """Live classroom dashboard — students × status × progress, with intervention queue."""
    from apps.classrooms.models import Membership
    from apps.realtime.models import ClassroomEvent, StudentStatus, StudentStatusKind

    classroom = get_object_or_404(Classroom, pk=classroom_id)
    ClassroomService.assert_teacher(classroom, request.user)

    memberships = (
        Membership.objects
        .filter(classroom=classroom)
        .select_related("student", "student__status")
        .order_by("student__username")
    )

    statuses = {
        s.student_id: s
        for s in StudentStatus.objects.filter(student_id__in=[m.student_id for m in memberships])
        .select_related("active_assignment")
    }

    rows = []
    counts = {k.value: 0 for k in StudentStatusKind}
    for m in memberships:
        s = statuses.get(m.student_id)
        kind = (s.status if s else StudentStatusKind.OFFLINE.value)
        counts[kind] = counts.get(kind, 0) + 1
        rows.append({"student": m.student, "status": s, "kind": kind})

    # Intervention queue: stuck/struggling, sorted by stuck_score desc.
    queue = sorted(
        [r for r in rows if r["kind"] in (StudentStatusKind.STUCK.value, StudentStatusKind.STRUGGLING.value)],
        key=lambda r: -(r["status"].stuck_score if r["status"] else 0.0),
    )

    active_attempts = (
        AssignmentAttempt.objects
        .filter(assignment__classroom=classroom, status=AttemptStatus.ACTIVE)
        .select_related("assignment", "student")
        .order_by("-started_at")
    )

    avg_progress = 0.0
    if rows:
        avg_progress = sum((r["status"].progress if r["status"] else 0) for r in rows) / len(rows)

    # Recent feed: classroom events filtered to user-visible signals.
    events = (
        ClassroomEvent.objects
        .filter(classroom=classroom)
        .select_related("user", "assignment")
        .order_by("-created_at")[:60]
    )

    return render(
        request,
        "assignments/monitor.html",
        {
            "classroom": classroom,
            "rows": rows,
            "counts": counts,
            "queue": queue,
            "active_attempts": active_attempts,
            "avg_progress": avg_progress,
            "events": events,
        },
    )


# ---- helpers ----
def _int_or_none(value):
    try:
        v = int(value)
        return v if v > 0 else None
    except (TypeError, ValueError):
        return None


def _dt_or_none(value):
    if not value:
        return None
    try:
        return timezone.datetime.fromisoformat(value).astimezone(timezone.get_current_timezone())
    except Exception:
        try:
            from datetime import datetime
            return datetime.fromisoformat(value)
        except Exception:
            return None
