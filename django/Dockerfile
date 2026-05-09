# =====================================================
# Django container — builds the web/worker/beat image.
# Multi-stage: builder installs deps, runtime is slim.
# =====================================================

ARG PYTHON_VERSION=3.12-slim-bookworm

# ---------- builder ----------
FROM python:${PYTHON_VERSION} AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY requirements/ /build/requirements/

ARG REQUIREMENTS=dev.txt
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip wheel \
    && /opt/venv/bin/pip install -r /build/requirements/${REQUIREMENTS}

# ---------- runtime ----------
FROM python:${PYTHON_VERSION} AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=educoder.settings.dev \
    PORT=8000

RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
        gettext \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system app \
    && useradd  --system --gid app --home /app app

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY --chown=app:app . /app

RUN mkdir -p /app/staticfiles /app/mediafiles \
    && chmod +x /app/scripts/entrypoint.sh \
    && chown -R app:app /app

USER app

EXPOSE 8000

ENTRYPOINT ["/app/scripts/entrypoint.sh"]

# Default command is overridden by docker-compose for each service
CMD ["sh", "-c", "uvicorn educoder.asgi:application --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
