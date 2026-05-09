from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import StudentBadge, StudentProgress


@login_required
def progress(request):
    progress, _ = StudentProgress.objects.get_or_create(student=request.user)
    badges = (
        StudentBadge.objects.filter(student=request.user)
        .select_related("badge")
        .order_by("-awarded_at")
    )
    next_level_xp = progress.level * 200
    progress_pct = min(100, int((progress.xp % 200) / 200 * 100)) if progress.xp else 0
    return render(
        request,
        "gamification/progress.html",
        {
            "progress": progress,
            "badges": badges,
            "next_level_xp": next_level_xp,
            "progress_pct": progress_pct,
        },
    )
