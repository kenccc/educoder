# educoder

Fully containerized Django coding sandbox for schools. Students write
code in the browser, teachers manage classrooms and assignments, and
**every line of student code runs inside an ephemeral Docker container
locked down with no network, capped CPU/memory, and a hard timeout.**

> Architecture rule: nothing executes on the host except the Docker
> daemon itself. Django, Postgres, Redis, Celery, the execution runner,
> and the per-submission sandbox containers all run in Docker.

---

## Quick start

```bash
cp .env.example .env                 # then edit secrets
make sandbox-image                   # build educoder/sandbox-python:latest
make build                           # build django-web + execution-runner
make up                              # start the stack
make migrate                         # apply migrations
make superuser                       # create an admin
```

Open http://localhost:8000.

---

## Render deployment

This repo includes a free-tier Render Blueprint at `render.yaml` for the
Django web service, managed Postgres, and Render Key Value (Redis-compatible)
Channels storage.

Before creating the Blueprint, decide where the execution runner will live.
Render does not provide a host Docker socket to services, so
`execution-runner` cannot spawn the sibling sandbox containers on Render. Run
the runner on infrastructure that supports Docker socket access, then set these
Render secrets when prompted:

- `EXECUTION_RUNNER_URL`: HTTPS URL of that external runner, reachable from Render.
- `EXECUTION_RUNNER_TOKEN`: strong shared secret used as the Bearer token.

The Blueprint lets Render generate `DJANGO_SECRET_KEY` and wires
`DATABASE_URL`, `REDIS_URL`, migrations, static collection, and `/healthz/`
health checks for the main app. Because free Render plans do not support
background workers, the Blueprint sets `CELERY_TASK_ALWAYS_EAGER=1`, so
submission grading runs inside the web request instead of in a separate Celery
worker.

Free-tier caveats:

- The web service spins down after idle periods, so first requests can be slow.
- Free Postgres expires after 30 days and has no backups.
- Free Key Value is in-memory only and can lose transient websocket/queue state.
- Long or busy grading workloads should move to a paid web + worker setup.

---

## FORPSI Basic Linux VPS

For the FORPSI Basic Linux VPS, use Ubuntu LTS and deploy the full Docker
Compose stack on the server. This is the recommended small production shape for
`educoder.cloud`.

Recommended VPS settings:

- OS: Ubuntu LTS
- DNS: point `educoder.cloud` and `www.educoder.cloud` A/AAAA records to the VPS
- Plesk: avoid it if optional; Docker Compose + Caddy is simpler here
- Open firewall ports: `22`, `80`, `443`

First deploy:

```bash
cp .env.vps.example .env
# edit .env and replace every secret
make prod-build
make prod-up
make superuser
make seed
```

The VPS compose file uses Caddy for automatic HTTPS, Django with two ASGI
workers, one Celery worker process, Postgres, Redis, the execution runner, and
the Python sandbox image. That keeps memory use reasonable on 4 GB RAM while
still running the real sandbox architecture.

---

## Service map

| Service            | Image                 | Role                                                           |
| ------------------ | --------------------- | -------------------------------------------------------------- |
| `django-web`       | `./django`            | ASGI app — HTTP + WebSocket (Channels). Renders HTMX templates. |
| `postgres`         | `postgres:16-alpine`  | Persistent storage.                                            |
| `redis`            | `redis:7-alpine`      | Celery broker + Channels layer.                                |
| `celery-worker`    | `./django`            | Async tasks (execution dispatch, grading, gamification).       |
| `celery-beat`      | `./django`            | Periodic jobs.                                                 |
| `execution-runner` | `./execution-runner`  | Spawns ephemeral sandbox containers. Mounts `docker.sock`.     |
| `nginx` (prod)     | `nginx:1.27-alpine`   | TLS termination, static files, websocket proxy.                |

---

## Data flow for one submission

```
 Browser
   │  POST /submissions/for/<assignment>/create/  (HTMX)
   ▼
 django-web ──▶ Submission row (PENDING)
   │
   │  Celery: apps.execution.tasks.run_submission
   ▼
 redis (queue: execution)
   │
   ▼
 celery-worker
   │  HTTP POST /run  (Bearer token)
   ▼
 execution-runner
   │  docker run --network=none --memory=128m --cpus=0.5 \
   │             --read-only --cap-drop=ALL --pids-limit=64 \
   │             --tmpfs /tmp educoder/sandbox-python
   │
   ▼
 sandbox container (one-shot)
   │  reads code from STDIN, executes, writes to stdout/stderr
   │  destroyed on exit
   ▼
 execution-runner returns {stdout, stderr, exit_code, timed_out, duration_ms}
   │
   ▼
 worker writes result to Submission row
   │  Channels group_send → "submission_<id>"
   ▼
 browser updates via HTMX poll OR websocket push
```

Grading and gamification are chained Celery tasks fired from
`services.execution.ExecutionService.run`.

---

## Folder layout

```
educoder/
├── docker-compose.yml          # full stack
├── docker-compose.prod.yml     # prod overrides (nginx, replicas, prod settings)
├── .env.example
├── Makefile
├── django/                     # django container build context
│   ├── Dockerfile              # multi-stage
│   ├── requirements/{base,dev,prod}.txt
│   ├── manage.py
│   ├── educoder/               # project package
│   │   ├── settings/{base,dev,prod}.py
│   │   ├── urls.py
│   │   ├── asgi.py             # http + websocket
│   │   ├── wsgi.py
│   │   ├── celery.py
│   │   └── routing.py
│   ├── apps/                   # django apps
│   │   ├── authentication/     # custom user (student/teacher/admin)
│   │   ├── classrooms/
│   │   ├── assignments/
│   │   ├── submissions/
│   │   ├── execution/          # celery tasks → execution-runner
│   │   ├── realtime/           # Channels consumers (no models)
│   │   └── gamification/
│   ├── services/               # business-logic layer (thin views)
│   ├── templates/              # base + per-app
│   ├── static/{css,js}/
│   └── scripts/entrypoint.sh
├── execution-runner/           # FastAPI sandbox spawner
│   ├── Dockerfile
│   └── app/{main.py,runner.py,requirements.txt}
├── sandbox-images/
│   └── python/                 # built as educoder/sandbox-python:latest
│       ├── Dockerfile
│       └── run-sandbox.sh
└── scripts/
    └── nginx.conf
```

---

## Architecture decisions

### Why a separate execution-runner service?

Putting the docker spawner inside Django would couple HTTP request
lifecycle to container scheduling, and would force Django to either
mount `docker.sock` (unacceptable blast radius — anyone with shell on
the web container could control the host docker daemon) or call out via
its own HTTP layer. We do the latter explicitly. Only **one** service
mounts the socket, and that service does nothing else.

### Why FastAPI for the runner?

Single-purpose service, no UI, no ORM, no migrations. FastAPI is light,
async-native, and pairs well with the docker SDK.

### Why Celery in front of execution?

Two reasons:
1. **Backpressure.** A surge of submissions doesn't stall the web
   request thread; jobs queue in Redis and run as workers free up.
2. **Retries.** Transient docker / network errors retry automatically
   without the student needing to resubmit.

### Why HTMX instead of React?

Schools deploy this to low-bandwidth Chromebooks. A 5kB HTMX dependency
+ Django templates ships less JS than a React bundle and removes the
SPA build step entirely. Live submission status uses HTMX polling
(simple) or websockets (richer); both work without a build pipeline.

### Sandbox hardening

Every per-execution container runs with:

| Flag                      | Why                                              |
| ------------------------- | ------------------------------------------------ |
| `--network=none`          | No exfiltration, no SSRF, no package fetches.    |
| `--read-only` + tmpfs /tmp| No persistent fs writes; tmpfs caps disk use.    |
| `--cap-drop=ALL`          | No privileged syscalls.                          |
| `--security-opt no-new-privileges` | Block setuid escalation.                |
| `--pids-limit=64`         | Stop fork bombs.                                 |
| `--memory` + `--cpus`     | Hard resource ceiling.                           |
| `--ulimit nofile/nproc`   | Stop fd / process exhaustion.                    |
| Non-root user in image    | Defense in depth against container escapes.     |
| `--rm` after run          | No stale state, no information leak across runs. |

Output is truncated to 64 KiB per stream to bound memory in Django.

### Settings split

`base.py` reads everything from env. `dev.py` enables debug toolbar and
relaxes validators. `prod.py` flips HTTPS-only flags, requires
`ALLOWED_HOSTS`, and wires Sentry if `SENTRY_DSN` is set.

### Realtime

Channels runs in the same `django-web` ASGI container as HTTP. The
channel layer is Redis (DB 1). Two consumers exist today: classroom
events (teacher dashboards) and per-submission updates (live execution
status).

---

## Running tests

```bash
make test
```

`pytest-django` is wired in `django/pytest.ini`.

---

## Production checklist

- [ ] Set strong `DJANGO_SECRET_KEY` and `EXECUTION_RUNNER_TOKEN`
- [ ] Set `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS`
- [ ] Use the prod compose overlay: `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d`
- [ ] Build sandbox image on every host that runs execution-runner
- [ ] Put nginx (or another TLS terminator) in front of django-web
- [ ] Replace Tailwind CDN with a built `tailwind.css` and run `collectstatic`
- [ ] Configure an off-host backup of the postgres volume
- [ ] Set `SENTRY_DSN` for error tracking
