#!/bin/sh
# Common entrypoint: wait for postgres when configured, optionally run
# migrations/static collection, then exec the real command.
set -eu

python - <<'PY'
import os, socket, time, sys
from urllib.parse import urlparse

database_url = os.environ.get("DATABASE_URL")
if database_url:
    parsed = urlparse(database_url)
    host = parsed.hostname
    port = parsed.port or 5432
else:
    host = os.environ.get("POSTGRES_HOST")
    port = int(os.environ.get("POSTGRES_PORT", "5432"))

if not host:
    sys.exit(0)

deadline = time.time() + 60
while time.time() < deadline:
    try:
        with socket.create_connection((host, port), timeout=2):
            sys.exit(0)
    except OSError:
        time.sleep(1)
print("postgres unreachable", file=sys.stderr); sys.exit(1)
PY

if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
  python manage.py migrate --noinput
fi

if [ "${RUN_COLLECTSTATIC:-0}" = "1" ]; then
  python manage.py collectstatic --noinput
fi

exec "$@"
