from django.contrib import admin

from .models import Assignment, AssignmentAttempt, AssignmentMetrics


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("title", "classroom", "language", "level", "due_at", "time_limit_minutes", "is_published")
    list_filter = ("language", "level", "is_published", "strict_mode")
    search_fields = ("title", "classroom__name")


@admin.register(AssignmentAttempt)
class AssignmentAttemptAdmin(admin.ModelAdmin):
    list_display = ("assignment", "student", "status", "started_at", "ended_at", "best_score", "is_correct", "cheat_event_count")
    list_filter = ("status", "is_correct")
    search_fields = ("student__username", "assignment__title")
    readonly_fields = ("started_at", "ended_at", "best_score", "is_correct")


@admin.register(AssignmentMetrics)
class AssignmentMetricsAdmin(admin.ModelAdmin):
    list_display = ("assignment", "students_started", "students_completed", "completion_rate", "median_solve_seconds", "computed_at")
    readonly_fields = ("computed_at",)
