from django.contrib import admin

from .models import Concept, ConceptMastery, Exercise, Hint, HintReveal, TestCase


class TestCaseInline(admin.TabularInline):
    model = TestCase
    extra = 0
    fk_name = "exercise"
    fields = ("ordering", "name", "stdin", "expected_stdout", "is_hidden", "weight")


class HintInline(admin.TabularInline):
    model = Hint
    extra = 1
    fields = ("level", "content", "penalty")


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ("title", "language", "level", "slug", "created_at")
    list_filter = ("language", "level", "concepts")
    search_fields = ("title", "slug", "tags")
    inlines = [TestCaseInline, HintInline]
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("concepts",)


@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    list_display = ("name", "exercise", "assignment", "is_hidden", "weight")
    list_filter = ("is_hidden",)
    search_fields = ("name",)


@admin.register(Concept)
class ConceptAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Hint)
class HintAdmin(admin.ModelAdmin):
    list_display = ("exercise", "level", "penalty")
    list_filter = ("exercise",)


@admin.register(HintReveal)
class HintRevealAdmin(admin.ModelAdmin):
    list_display = ("attempt", "hint", "student", "revealed_at")
    list_filter = ("revealed_at",)


@admin.register(ConceptMastery)
class ConceptMasteryAdmin(admin.ModelAdmin):
    list_display = ("student", "concept", "score", "attempts", "last_activity")
    list_filter = ("concept",)
