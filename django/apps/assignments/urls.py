from django.urls import path

from . import views

app_name = "assignments"

urlpatterns = [
    path("<int:pk>/",                         views.assignment_detail,            name="detail"),
    path("classroom/<int:classroom_id>/new/", views.assignment_new,               name="new"),
    path("classroom/<int:classroom_id>/from-exercise/", views.assignment_create_from_exercise, name="create_from_exercise"),
    path("classroom/<int:classroom_id>/custom/",        views.assignment_create_custom,        name="create_custom"),
    path("<int:assignment_id>/start/",        views.attempt_start,                name="start"),
    path("attempt/<int:attempt_id>/",         views.attempt_ide,                  name="attempt"),
    path("attempt/<int:attempt_id>/snapshot/", views.attempt_snapshot,            name="attempt_snapshot"),
    path("classroom/<int:classroom_id>/leaderboard/", views.classroom_leaderboard, name="leaderboard"),
    path("classroom/<int:classroom_id>/monitor/",     views.classroom_monitor,    name="monitor"),
    path("attempt/<int:attempt_id>/timeline/",        views.attempt_timeline,     name="attempt_timeline"),
    path("<int:assignment_id>/analytics/",            views.assignment_analytics, name="analytics"),
    path("<int:assignment_id>/students/",             views.assignment_students,  name="students"),
]
