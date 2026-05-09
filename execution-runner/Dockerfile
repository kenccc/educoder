# =====================================================
# execution-runner — separate microservice (FastAPI).
# Receives RunRequest from Django/Celery and spawns
# ephemeral docker SIBLING containers for student code.
#
# Mounts /var/run/docker.sock (Docker-out-of-Docker).
# Never executes student code in this container itself.
# =====================================================
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY app/requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

COPY app /app

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
