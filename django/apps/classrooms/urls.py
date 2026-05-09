from django.urls import path

from . import views

app_name = "classrooms"

urlpatterns = [
    path("",            views.classroom_list,   name="list"),
    path("create/",     views.classroom_create, name="create"),
    path("join/",       views.classroom_join,   name="join"),
    path("<int:pk>/",   views.classroom_detail, name="detail"),
    path("<int:pk>/students/<int:student_id>/", views.student_detail, name="student_detail"),
]
