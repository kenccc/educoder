# =====================================================
# educoder/sandbox-python — minimal image used for ONE
# student code execution. Spawned by execution-runner.
# Build:  docker build -t educoder/sandbox-python:latest .
# =====================================================
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Non-root user — student code runs as 'sandbox', uid 1000
RUN groupadd --system sandbox \
    && useradd --system --gid sandbox --create-home --home-dir /home/sandbox sandbox

COPY run-sandbox.sh /usr/local/bin/run-sandbox.sh
RUN chmod 0755 /usr/local/bin/run-sandbox.sh

USER sandbox
WORKDIR /home/sandbox

# The runner overrides command — keep a sane default for manual debug.
CMD ["/usr/local/bin/run-sandbox.sh"]
