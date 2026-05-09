"""Root URL config."""
from django.conf import settings
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from django.views.generic import RedirectView


def healthz(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("healthz/", healthz, name="healthz"),
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(pattern_name="classrooms:list", permanent=False)),
    path("auth/",        include(("apps.authentication.urls", "auth"),         namespace="auth")),
    path("classrooms/",  include(("apps.classrooms.urls",     "classrooms"),   namespace="classrooms")),
    path("library/",     include(("apps.exercises.urls",      "exercises"),    namespace="exercises")),
    path("assignments/", include(("apps.assignments.urls",    "assignments"),  namespace="assignments")),
    path("submissions/", include(("apps.submissions.urls",    "submissions"),  namespace="submissions")),
    path("gamification/",include(("apps.gamification.urls",   "gamification"), namespace="gamification")),
]

if settings.DEBUG:
    try:
        import debug_toolbar
        urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
    except ImportError:
        pass
