from __future__ import annotations

from datetime import date

from django.db import transaction
from django.db.models import Count, F, Max, Sum, Q

from apps.assignments.models import Assignment
from apps.classrooms.models import Classroom
from apps.exercises.models import LEVEL_XP, Level
from apps.gamification.models import Badge, StudentBadge, StudentProgress
from apps.submissions.models import Submission, SubmissionStatus


XP_PER_RUN = 5          # any run that finishes
XP_PER_PASS = 25        # per testcase passed
XP_FIRST_TRY_BONUS = 50 # solved on first submission within attempt
XP_PER_LEVEL = 200


def _xp_for_submission(submission: Submission) -> int:
    if submission.status != SubmissionStatus.SUCCESS:
        return XP_PER_RUN if submission.passed_count else 0

    level = (submission.assignment.level or "").lower()
    base = LEVEL_XP.get(level, 50) if submission.is_correct else 0
    per_case = XP_PER_PASS * (submission.passed_count or 0)
    earned = XP_PER_RUN + per_case + base

    # Subtract any HintReveal penalties for this attempt — capped at the earned total.
    if submission.attempt_id:
        from apps.exercises.models import HintReveal
        penalty = sum(
            r.hint.penalty
            for r in HintReveal.objects.filter(attempt_id=submission.attempt_id).select_related("hint")
        )
        earned = max(0, earned - penalty)
    return earned


class GamificationService:
    @staticmethod
    def award_for_submission(submission_id: str) -> None:
        # Claim + XP work share one transaction so a failure rolls the
        # xp_awarded flag back along with the partial progress write —
        # otherwise a Celery retry would see the flag set and skip,
        # silently losing the XP.
        with transaction.atomic():
            claimed = Submission.objects.filter(
                pk=submission_id, xp_awarded=False
            ).update(xp_awarded=True)
            if not claimed:
                return

            submission = (
                Submission.objects
                .select_related("assignment", "assignment__exercise", "student", "attempt")
                .get(pk=submission_id)
            )

            gained = _xp_for_submission(submission)
            # Persist gained XP on the submission so the UI can show "+X XP"
            # right after a successful run, even before StudentProgress reloads.
            Submission.objects.filter(pk=submission_id).update(xp_earned=gained)
            if not gained:
                return

            progress, _ = StudentProgress.objects.select_for_update().get_or_create(
                student=submission.student,
            )
            progress.xp = (progress.xp or 0) + gained
            progress.level = max(1, progress.xp // XP_PER_LEVEL + 1)

            today = date.today()
            if progress.last_activity == today:
                pass
            elif progress.last_activity and (today - progress.last_activity).days == 1:
                progress.streak_days += 1
            else:
                progress.streak_days = 1
            progress.last_activity = today
            progress.save()

        GamificationService._maybe_award_badges(submission)
        GamificationService._bump_concept_mastery(submission)

    @staticmethod
    def _bump_concept_mastery(submission: Submission) -> None:
        """Update ConceptMastery via EMA over passed/total ratio for this submission."""
        from datetime import datetime, timezone as _tz

        from apps.exercises.models import ConceptMastery
        if not submission.assignment.exercise_id or submission.total_count == 0:
            return
        ratio = (submission.passed_count or 0) / submission.total_count
        concepts = list(submission.assignment.exercise.concepts.all())
        if not concepts:
            return
        with transaction.atomic():
            for concept in concepts:
                cm, _ = ConceptMastery.objects.select_for_update().get_or_create(
                    student=submission.student, concept=concept,
                )
                # EMA with α=0.3 — balances recency vs. stability.
                cm.score = round(0.7 * cm.score + 0.3 * ratio, 4)
                cm.attempts = (cm.attempts or 0) + 1
                cm.last_activity = datetime.now(_tz.utc)
                cm.save()

    @staticmethod
    def _maybe_award_badges(submission: Submission) -> None:
        if submission.is_correct:
            badges_unlocked = []
            student_correct = Submission.objects.filter(
                student=submission.student, is_correct=True
            ).count()

            milestones = {
                1:  ("first_solve",   "First Solve",      "Pass your first task"),
                10: ("ten_solves",    "Persistent",       "Solve 10 tasks"),
                25: ("quarter",       "Twenty-Five",      "Solve 25 tasks"),
            }
            for n, (code, name, desc) in milestones.items():
                if student_correct >= n:
                    badge, _ = Badge.objects.get_or_create(
                        code=code, defaults={"name": name, "description": desc},
                    )
                    StudentBadge.objects.get_or_create(student=submission.student, badge=badge)
                    badges_unlocked.append(code)

            level = (submission.assignment.level or "").lower()
            if level == Level.HARD:
                badge, _ = Badge.objects.get_or_create(
                    code="hard_solver",
                    defaults={"name": "Hard Mode", "description": "Solve a Hard task"},
                )
                StudentBadge.objects.get_or_create(student=submission.student, badge=badge)


class LeaderboardService:
    @staticmethod
    def for_classroom(classroom: Classroom):
        """Per-classroom student ranking — XP from correct submissions in this room."""
        rows = (
            Submission.objects
            .filter(
                assignment__classroom=classroom,
                status=SubmissionStatus.SUCCESS,
            )
            .values("student__id", "student__username", "student__display_name")
            .annotate(
                solved=Count("id", filter=Q(is_correct=True), distinct=True),
                attempts=Count("id"),
                xp=Sum("score"),
                last_solve=Max("completed_at"),
            )
            .order_by("-xp", "-solved", "last_solve")
        )
        return list(rows)
