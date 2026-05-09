from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.assignments.models import Assignment, AssignmentAttempt
from services.submissions import AttemptService

from .models import Exercise, Hint, HintReveal, Language, Level


PAGE_SIZE = 20


@login_required
def library(request):
    """Public exercise library — students can self-practice from here."""
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

    paginator = Paginator(qs, PAGE_SIZE)
    page = paginator.get_page(request.GET.get("page"))

    params = request.GET.copy()
    params.pop("page", None)
    qs_no_page = params.urlencode()

    return render(
        request,
        "exercises/library.html",
        {
            "page_obj": page,
            "paginator": paginator,
            "exercises": page.object_list,
            "languages": Language.choices,
            "levels": Level.choices,
            "selected_language": language,
            "selected_level": level,
            "q": q,
            "qs_no_page": qs_no_page,
            "total": paginator.count,
        },
    )


@login_required
@require_POST
def practice_start(request, exercise_id: int):
    """Get-or-create a solo Assignment for (student, exercise), then start an attempt."""
    exercise = get_object_or_404(Exercise, pk=exercise_id)

    assignment, _ = Assignment.objects.get_or_create(
        classroom=None,
        solo_owner=request.user,
        exercise=exercise,
        defaults={
            "title": exercise.title,
            "description": exercise.prompt_md,
            "language": exercise.language,
            "level": exercise.level,
            "starter_code": exercise.starter_code,
            "strict_mode": False,
            "is_published": True,
        },
    )

    attempt = AttemptService.get_or_create(assignment=assignment, student=request.user)
    return redirect("assignments:attempt", attempt_id=attempt.pk)


@login_required
@require_POST
def reveal_hint(request, attempt_id: int, hint_id: int):
    """Reveal a hint for the active attempt — idempotent. Penalty applied at submission time."""
    attempt = get_object_or_404(
        AssignmentAttempt.objects.select_related("assignment", "assignment__exercise"),
        pk=attempt_id,
    )
    if attempt.student_id != request.user.id:
        raise PermissionDenied()

    exercise_id = attempt.assignment.exercise_id
    hint = get_object_or_404(Hint, pk=hint_id, exercise_id=exercise_id)

    HintReveal.objects.get_or_create(
        attempt=attempt, hint=hint,
        defaults={"student": request.user},
    )

    from apps.realtime.models import EventType
    from services.events import EventService
    EventService.record(
        user=request.user,
        assignment=attempt.assignment,
        attempt=attempt,
        type=EventType.HINT_OPEN.value,
        payload={"hint_id": hint.id, "level": hint.level, "penalty": hint.penalty},
    )
    return JsonResponse({
        "ok": True,
        "level": hint.level,
        "content": hint.content,
        "penalty": hint.penalty,
    })
