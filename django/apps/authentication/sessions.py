"""UUID-keyed session store. Drop-in replacement for the DB session backend."""
from __future__ import annotations

import uuid

from django.contrib.sessions.backends.db import SessionStore as DBSessionStore


class SessionStore(DBSessionStore):
    def _get_new_session_key(self) -> str:
        while True:
            key = uuid.uuid4().hex
            if not self.exists(key):
                return key
