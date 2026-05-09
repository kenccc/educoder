from django.contrib import admin

from .models import CheatEvent, ClassroomEvent, CodeSnapshot, StudentStatus


@admin.register(CheatEvent)
class CheatEventAdmin(admin.ModelAdmin):
    list_display = ("student", "kind", "severity", "attempt", "occurred_at")
    list_filter = ("kind", "severity")
    search_fields = ("student__username",)
    readonly_fields = ("payload", "occurred_at")


@admin.register(ClassroomEvent)
class ClassroomEventAdmin(admin.ModelAdmin):
    list_display = ("user", "type", "classroom", "assignment", "created_at")
    list_filter = ("type", "classroom")
    search_fields = ("user__username", "type")
    readonly_fields = ("payload", "created_at")


@admin.register(CodeSnapshot)
class CodeSnapshotAdmin(admin.ModelAdmin):
    list_display = ("attempt", "trigger", "created_at")
    list_filter = ("trigger",)


@admin.register(StudentStatus)
class StudentStatusAdmin(admin.ModelAdmin):
    list_display = ("student", "status", "stuck_score", "progress", "classroom", "updated_at")
    list_filter = ("status",)
    search_fields = ("student__username",)
