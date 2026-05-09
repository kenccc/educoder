"""Production settings — hardened security, must run behind TLS proxy."""
from .base import *  # noqa: F401,F403
from .base import env, env_list

DEBUG = False
render_hostname = env("RENDER_EXTERNAL_HOSTNAME", "")
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS")
if render_hostname and render_hostname not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(render_hostname)
if not ALLOWED_HOSTS:
    raise RuntimeError("DJANGO_ALLOWED_HOSTS must be set in production")

# ---- Security ----
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")
if render_hostname:
    render_origin = f"https://{render_hostname}"
    if render_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(render_origin)

if (
    len(SECRET_KEY) < 32
    or SECRET_KEY.startswith("django-insecure-")
    or "replace" in SECRET_KEY.lower()
    or SECRET_KEY in {
    "replace-me-with-strong-random-value",
    "insecure-dev-secret-change-me",
    }
):
    raise RuntimeError("DJANGO_SECRET_KEY must be a strong production secret")

if (
    len(EXECUTION_RUNNER_TOKEN) < 32
    or "replace" in EXECUTION_RUNNER_TOKEN.lower()
    or EXECUTION_RUNNER_TOKEN in {"dev-token", "replace-with-shared-secret", ""}
):
    raise RuntimeError("EXECUTION_RUNNER_TOKEN must be set to a strong shared secret")

# ---- Email (SMTP) ----
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", "")
EMAIL_PORT = int(env("EMAIL_PORT", "587"))
EMAIL_HOST_USER = env("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = True

# ---- Sentry (optional) ----
SENTRY_DSN = env("SENTRY_DSN", "")
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), CeleryIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=False,
    )
