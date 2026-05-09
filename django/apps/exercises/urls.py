from django.urls import path

from . import views

app_name = "exercises"

urlpatterns = [
    path("",                              views.library,         name="library"),
    path("<int:exercise_id>/practice/",   views.practice_start,  name="practice"),
    path("attempt/<int:attempt_id>/hint/<int:hint_id>/reveal/", views.reveal_hint, name="reveal_hint"),
]
