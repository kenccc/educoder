"""Development settings — overrides base.py for local dev."""
import os

os.environ.setdefault("DJANGO_SECRET_KEY", "insecure-dev-secret-change-me")

from .base import *  # noqa: F401,F403,E402
from .base import INSTALLED_APPS, MIDDLEWARE, env  # noqa: E402

DEBUG = True
ALLOWED_HOSTS = ["*"]

# In dev, serve static files via Django's staticfiles app (no manifest hashing).
# Manifest storage requires `collectstatic` to run before any static URL resolves,
# which is awkward locally and was breaking /static/css/app.css loads.
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# Email to console
EMAIL_BACKEND = env("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")

# Debug toolbar — only in dev
INSTALLED_APPS += ["debug_toolbar", "django_extensions"]
MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")

INTERNAL_IPS = ["127.0.0.1"]
DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": lambda request: False}

# Less aggressive password validators in dev
AUTH_PASSWORD_VALIDATORS = []

# CSRF allow-list for compose hostnames
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8090", "http://127.0.0.1:8090",
    "http://localhost",      "http://127.0.0.1",
]
