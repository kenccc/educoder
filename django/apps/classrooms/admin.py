from django.contrib import admin

from .models import Classroom, Membership


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ("name", "teacher", "join_code", "is_archived", "created_at")
    search_fields = ("name", "join_code")
    list_filter = ("is_archived",)


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("classroom", "student", "joined_at")
