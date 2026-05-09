"""
Base Django settings — shared by dev and prod.

Environment-driven. Reads only from os.environ. Two layers above
(dev.py / prod.py) override anything that needs to differ.
"""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlparse

# ---------- Paths ----------
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # /app


def env(key: str, default: str | None = None) -> str:
    val = os.environ.get(key, default)
    if val is None:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return val


def env_bool(key: str, default: bool = False) -> bool:
    return os.environ.get(key, str(int(default))).lower() in ("1", "true", "yes", "on")


def env_list(key: str, default: str = "") -> list[str]:
    raw = os.environ.get(key, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def database_from_url(url: str) -> dict:
    parsed = urlparse(url)
    if parsed.scheme not in {"postgres", "postgresql"}:
        raise RuntimeError("DATABASE_URL must use postgres:// or postgresql://")

    options = dict(parse_qsl(parsed.query))
    config = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": unquote((parsed.path or "").lstrip("/")),
        "USER": unquote(parsed.username or ""),
        "PASSWORD": unquote(parsed.password or ""),
        "HOST": parsed.hostname or "",
        "PORT": str(parsed.port or 5432),
        "CONN_MAX_AGE": 60,
    }
    if options.get("sslmode"):
        config["OPTIONS"] = {"sslmode": options["sslmode"]}
    return config


# ---------- Core ----------
SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env_bool("DJANGO_DEBUG", False)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")

INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "channels",
    "django_htmx",
    "django_celery_beat",
    "django_celery_results",
    "widget_tweaks",

    # First-party apps
    "apps.authentication",
    "apps.classrooms",
    "apps.exercises",
    "apps.assignments",
    "apps.submissions",
    "apps.execution",
    "apps.realtime",
    "apps.gamification",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

ROOT_URLCONF = "educoder.urls"
WSGI_APPLICATION = "educoder.wsgi.application"
ASGI_APPLICATION = "educoder.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ---------- Database ----------
DATABASE_URL = os.environ.get("DATABASE_URL")
DATABASES = {
    "default": database_from_url(DATABASE_URL) if DATABASE_URL else {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": env("POSTGRES_HOST", "postgres"),
        "PORT": env("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": 60,
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "authentication.User"

# ---------- Auth ----------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LOGIN_URL = "auth:login"
LOGIN_REDIRECT_URL = "classrooms:list"
LOGOUT_REDIRECT_URL = "auth:login"

# Sliding session: cookie refreshes on every request (SESSION_SAVE_EVERY_REQUEST).
# Cookie age kept under 1y so privacy heuristics (browser tracking-protection)
# don't silently drop the cookie. With sliding refresh, active users stay logged in.
SESSION_ENGINE = "apps.authentication.sessions"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 30  # 30 days
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# ---------- I18N ----------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ---------- Static / media ----------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "mediafiles"

# ---------- Channels (websockets) ----------
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [env("CHANNEL_LAYER_URL", env("REDIS_URL", "redis://redis:6379/1"))],
        },
    },
}

# ---------- Celery ----------
CELERY_BROKER_URL = env("CELERY_BROKER_URL", env("REDIS_URL", "redis://redis:6379/2"))
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", "django-db")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 60
CELERY_TASK_SOFT_TIME_LIMIT = 50
CELERY_TASK_ALWAYS_EAGER = env_bool("CELERY_TASK_ALWAYS_EAGER", False)
CELERY_TASK_EAGER_PROPAGATES = True

CELERY_TASK_ROUTES = {
    "apps.execution.tasks.*":    {"queue": "execution"},
    "apps.gamification.tasks.*": {"queue": "default"},
    "apps.submissions.tasks.*":  {"queue": "grading"},
    "apps.realtime.tasks.*":     {"queue": "default"},
    "apps.assignments.tasks.*":  {"queue": "default"},
}

CELERY_BEAT_SCHEDULE = {
    "compute-student-status-30s": {
        "task": "apps.realtime.tasks.compute_student_status",
        "schedule": 30.0,
    },
    "aggregate-assignment-metrics-5m": {
        "task": "apps.assignments.tasks.aggregate_assignment_metrics",
        "schedule": 300.0,
    },
}

# ---------- Execution runner ----------
EXECUTION_RUNNER_URL = env("EXECUTION_RUNNER_URL", "http://execution-runner:8080")
EXECUTION_RUNNER_TOKEN = env("EXECUTION_RUNNER_TOKEN", "dev-token")
SANDBOX_TIMEOUT_SECONDS = int(env("SANDBOX_TIMEOUT_SECONDS", "5"))

# ---------- Logging ----------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "[{asctime}] {levelname} {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "celery": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "apps":   {"handlers": ["console"], "level": "DEBUG", "propagate": False},
    },
}
