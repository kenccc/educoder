from django.contrib import admin

from .models import Badge, StudentBadge, StudentProgress


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ("code", "name")


@admin.register(StudentProgress)
class StudentProgressAdmin(admin.ModelAdmin):
    list_display = ("student", "xp", "level", "streak_days")


@admin.register(StudentBadge)
class StudentBadgeAdmin(admin.ModelAdmin):
    list_display = ("student", "badge", "awarded_at")
