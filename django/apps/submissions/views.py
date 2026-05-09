from __future__ import annotations

import json

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods, require_POST

from apps.assignments.models import Assignment, AssignmentAttempt
from apps.exercises.models import Language
from services.submissions import AttemptService, SubmissionService

from .models import Submission, TestRun


@login_required
@require_POST
def submission_create(request, attempt_id: int):
    attempt = get_object_or_404(
        AssignmentAttempt.objects.select_related("assignment"),
        pk=attempt_id,
    )
    if attempt.student_id != request.user.id:
        raise PermissionDenied()

    try:
        submission = SubmissionService.create_and_dispatch(
            assignment=attempt.assignment,
            student=request.user,
            code=request.POST.get("code", ""),
            attempt=attempt,
        )
    except (ValueError, ValidationError) as exc:
        return HttpResponseBadRequest(str(exc))
    except PermissionDenied as exc:
        return HttpResponseBadRequest(str(exc))

    return render(request, "submissions/_status.html", {"submission": submission})


@login_required
@require_POST
def submission_web_results(request, submission_id):
    """Client-side iframe assertion runner posts results back here."""
    submission = get_object_or_404(
        Submission.objects.select_related("assignment", "student"),
        pk=submission_id,
    )
    if submission.student_id != request.user.id:
        raise PermissionDenied()
    if submission.assignment.language != Language.WEB:
        return HttpResponseBadRequest("not a web submission")

    try:
        payload = json.loads(request.body or b"{}")
    except ValueError:
        return HttpResponseBadRequest("bad json")
    SubmissionService.record_web_result(submission=submission, results=payload.get("results", []))
    return render(request, "submissions/_status.html", {"submission": submission})


@login_required
def submission_status(request, pk):
    submission = get_object_or_404(Submission, pk=pk, student=request.user)
    return render(request, "submissions/_status.html", {"submission": submission})


@login_required
def submission_detail(request, pk):
    submission = get_object_or_404(
        Submission.objects.select_related("assignment", "attempt", "student"),
        pk=pk,
    )
    a = submission.assignment
    is_teacher_of_room = (
        a.classroom_id is not None and a.classroom.teacher_id == request.user.id
    )
    if submission.student_id != request.user.id and not is_teacher_of_room:
        raise PermissionDenied()
    runs = submission.test_runs.all()
    return render(request, "submissions/detail.html", {"submission": submission, "runs": runs})
