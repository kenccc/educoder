from django.urls import path

from . import views

app_name = "submissions"

urlpatterns = [
    path("attempt/<int:attempt_id>/create/",       views.submission_create,      name="create"),
    path("<uuid:pk>/status/",                       views.submission_status,      name="status"),
    path("<uuid:pk>/detail/",                       views.submission_detail,      name="detail"),
    path("<uuid:submission_id>/web-results/",       views.submission_web_results, name="web_results"),
]
