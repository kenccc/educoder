"""SandboxRunner — spawns one ephemeral docker container per code run.

Wire protocol with the sandbox image:
  - Code is passed in env var STUDENT_CODE_B64 (base64-encoded).
  - The container's STDIN is the program's actual stdin.
  - Sandbox script decodes the env var, writes to /tmp, then `exec python`.
"""
from __future__ import annotations

import base64
import logging
from dataclasses import dataclass

import docker
from docker.errors import ContainerError, ImageNotFound
from docker.types import Ulimit

logger = logging.getLogger("execution-runner.runner")

_MAX_OUTPUT_BYTES = 64 * 1024


@dataclass
class SandboxResult:
    stdout: str
    stderr: str
    exit_code: int | None
    timed_out: bool


class SandboxRunner:
    def __init__(
        self,
        *,
        image: str,
        cpu_limit: float,
        memory_limit: str,
        network: str = "none",
    ) -> None:
        self.image = image
        self.cpu_limit = cpu_limit
        self.memory_limit = memory_limit
        self.network = network
        self.client = docker.from_env()

    def run(self, *, code: str, stdin: str, timeout: int, job_id: str) -> SandboxResult:
        code_b64 = base64.b64encode(code.encode("utf-8")).decode("ascii")

        try:
            container = self.client.containers.create(
                self.image,
                command=["/usr/local/bin/run-sandbox.sh"],
                stdin_open=True,
                tty=False,
                detach=True,
                name=f"educoder-sandbox-{job_id}",

                # ------ resource limits ------
                mem_limit=self.memory_limit,
                memswap_limit=self.memory_limit,
                pids_limit=64,
                nano_cpus=int(self.cpu_limit * 1e9),
                ulimits=[
                    Ulimit(name="nofile", soft=64, hard=64),
                    Ulimit(name="nproc",  soft=64, hard=64),
                ],

                # ------ isolation ------
                network_mode=self.network,
                read_only=True,
                tmpfs={"/tmp": "rw,noexec,nosuid,size=16m"},
                cap_drop=["ALL"],
                security_opt=["no-new-privileges:true"],

                environment={
                    "PYTHONDONTWRITEBYTECODE": "1",
                    "PYTHONUNBUFFERED": "1",
                    "STUDENT_CODE_B64": code_b64,
                },
            )
        except ImageNotFound as exc:
            raise RuntimeError(
                f"Sandbox image '{self.image}' not found. "
                "Build it with: make sandbox-image"
            ) from exc

        try:
            container.start()
            sock = container.attach_socket(params={"stdin": 1, "stream": 1})
            if stdin:
                sock._sock.sendall(stdin.encode("utf-8"))  # noqa: SLF001
            sock._sock.shutdown(1)  # noqa: SLF001
            sock.close()

            try:
                exit_status = container.wait(timeout=timeout)
                exit_code = exit_status.get("StatusCode")
                timed_out = False
            except Exception:
                logger.warning("sandbox timeout job=%s", job_id)
                try:
                    container.kill()
                except Exception:  # noqa: BLE001
                    pass
                exit_code = None
                timed_out = True

            stdout = container.logs(stdout=True, stderr=False)[:_MAX_OUTPUT_BYTES].decode("utf-8", "replace")
            stderr = container.logs(stdout=False, stderr=True)[:_MAX_OUTPUT_BYTES].decode("utf-8", "replace")

            return SandboxResult(stdout=stdout, stderr=stderr, exit_code=exit_code, timed_out=timed_out)
        except ContainerError as exc:
            return SandboxResult(stdout="", stderr=str(exc), exit_code=exc.exit_status, timed_out=False)
        finally:
            try:
                container.remove(force=True)
            except Exception:  # noqa: BLE001
                logger.warning("could not remove sandbox container job=%s", job_id)
