"""Celery application factory.

Reads broker/result config from Django settings. Worker container
runs `celery -A educoder worker` to consume queues.
"""
from __future__ import annotations

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "educoder.settings.dev")

app = Celery("educoder")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self) -> None:
    print(f"Request: {self.request!r}")
