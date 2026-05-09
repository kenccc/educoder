"""WSGI config — kept for management commands; runtime uses ASGI."""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "educoder.settings.dev")
application = get_wsgi_application()
