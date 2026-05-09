#!/bin/sh
# Decode STUDENT_CODE_B64 to /tmp/student.py, then exec python with the
# container's stdin as the program's actual stdin. Runner sends program
# stdin over the docker attach socket before container start.
set -eu

if [ -z "${STUDENT_CODE_B64:-}" ]; then
  echo "missing STUDENT_CODE_B64" >&2
  exit 64
fi

CODE_FILE="$(mktemp /tmp/student.XXXXXX.py)"
printf '%s' "$STUDENT_CODE_B64" | base64 -d > "$CODE_FILE"

unset STUDENT_CODE_B64
exec python -I -B "$CODE_FILE"
