"""execution-runner — HTTP service that spawns ephemeral docker sandboxes
for one untrusted code execution at a time.

Endpoints:
  POST /run    — synchronous run of a (code, stdin) pair
  GET  /health — liveness probe
"""
from __future__ import annotations

import logging
import os
import secrets
import time
import uuid
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

from runner import SandboxResult, SandboxRunner

logger = logging.getLogger("execution-runner")
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))

app = FastAPI(title="educoder execution-runner", version="0.2.0")

EXPECTED_TOKEN = os.environ.get("EXECUTION_RUNNER_TOKEN", "")
if (
    EXPECTED_TOKEN in {"", "dev-token", "replace-with-shared-secret"}
    or len(EXPECTED_TOKEN) < 32
    or "replace" in EXPECTED_TOKEN.lower()
) and os.environ.get("RUNNER_ENV") == "production":
    raise RuntimeError("EXECUTION_RUNNER_TOKEN must be set in production")


def require_token(authorization: str = Header(default="")) -> None:
    expected = f"Bearer {EXPECTED_TOKEN}"
    if not secrets.compare_digest(authorization, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")


class RunRequest(BaseModel):
    submission_id: str
    language: Literal["python"] = "python"
    code: str = Field(..., max_length=64 * 1024)
    stdin: str = Field(default="", max_length=64 * 1024)
    timeout_seconds: int = Field(default=5, ge=1, le=30)


class RunResponse(BaseModel):
    job_id: str
    submission_id: str
    stdout: str
    stderr: str
    exit_code: int | None
    duration_ms: int
    timed_out: bool


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/run", response_model=RunResponse, dependencies=[Depends(require_token)])
def run(req: RunRequest) -> RunResponse:
    job_id = uuid.uuid4().hex
    logger.info("run job=%s submission=%s lang=%s", job_id, req.submission_id, req.language)

    runner = SandboxRunner(
        image=os.environ.get("SANDBOX_IMAGE", "educoder/sandbox-python:latest"),
        cpu_limit=float(os.environ.get("SANDBOX_CPU_LIMIT", "0.5")),
        memory_limit=os.environ.get("SANDBOX_MEMORY_LIMIT", "128m"),
        network=os.environ.get("SANDBOX_NETWORK", "none"),
    )

    started = time.monotonic()
    try:
        result: SandboxResult = runner.run(
            code=req.code,
            stdin=req.stdin,
            timeout=req.timeout_seconds,
            job_id=job_id,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("sandbox run failed job=%s", job_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    duration_ms = int((time.monotonic() - started) * 1000)

    return RunResponse(
        job_id=job_id,
        submission_id=req.submission_id,
        stdout=result.stdout,
        stderr=result.stderr,
        exit_code=result.exit_code,
        duration_ms=duration_ms,
        timed_out=result.timed_out,
    )
