from django.contrib import admin

from .models import ExecutionLog


@admin.register(ExecutionLog)
class ExecutionLogAdmin(admin.ModelAdmin):
    list_display = ("id", "submission_id", "image", "exit_code", "timed_out", "started_at")
    list_filter = ("timed_out",)
    search_fields = ("submission_id",)
