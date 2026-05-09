from django.contrib import admin

from .models import Submission, TestRun


class TestRunInline(admin.TabularInline):
    model = TestRun
    extra = 0
    readonly_fields = ("name", "passed", "is_hidden", "actual_stdout", "expected_stdout", "error", "runtime_ms")
    can_delete = False


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("id", "assignment", "student", "status", "passed_count", "total_count", "score", "created_at")
    list_filter = ("status",)
    search_fields = ("student__username", "assignment__title")
    readonly_fields = ("id", "stdout", "stderr", "exit_code", "duration_ms", "completed_at")
    inlines = [TestRunInline]


@admin.register(TestRun)
class TestRunAdmin(admin.ModelAdmin):
    list_display = ("submission", "name", "passed", "is_hidden", "runtime_ms")
    list_filter = ("passed", "is_hidden")
