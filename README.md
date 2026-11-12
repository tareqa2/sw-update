# SW Update Manager

A Flask web app and REST API that tracks software versions (OS, Backend, Database, Frontend) across lab devices, decides whether a requested change is an **upgrade**, **downgrade** or **no change**, and keeps a full update history per device.

This repo holds the **application**: source code, tests and Dockerfile.
Infrastructure (Kubernetes manifests, nginx, CI runner) lives in **[sw-update-devops](https://github.com/tareqa2/sw-update-devops)**.

![CI/CD](https://github.com/tareqa2/sw-update/actions/workflows/ci.yml/badge.svg)
![Nightly regression](https://github.com/tareqa2/sw-update/actions/workflows/nightly-regression.yml/badge.svg)

---

## Architecture

```
Browser ──► nginx (2 replicas, NodePort 30080) ──► sw-backend Service ──► Flask + gunicorn (1 replica) ──► PVC /data (CSV files)
                                                                                 ▲
                                                             Prometheus scrapes /metrics
```

The backend is split into layers, each with one job:

| Module | Responsibility |
|---|---|
| `app/__init__.py` | `create_app()` factory - builds a fresh app (tests use one per test) |
| `app/config.py` | All settings from environment variables - nothing hardcoded |
| `app/versions.py` | Pure logic: validate and compare version strings |
| `app/services.py` | Business rules: device/component/branch/commit validation, update planning |
| `app/storage.py` | CSV persistence with atomic writes and file locking |
| `app/api.py` | REST API under `/api/v1` (JSON in, JSON out) |
| `app/web.py` | Server-rendered UI (Overview / Update / History) |
| `app/errors.py` | Every error becomes a clean JSON `4xx/5xx` - never a stack trace |
| `app/health.py` | `/healthz` (liveness) and `/readyz` (readiness - checks storage) |
| `app/metrics.py` | Prometheus metrics on `/metrics` |

## API

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/master` | Master (target) versions |
| GET | `/api/v1/devices` | All devices and whether each matches master |
| GET | `/api/v1/devices/{id}` | Installed versions of one device |
| POST | `/api/v1/devices/{id}/plan` | Dry run: what would change |
| POST | `/api/v1/devices/{id}/updates` | Apply an update (`201`) and log it |
| GET | `/api/v1/devices/{id}/history?component=&action=&limit=` | Update history, newest first |
| GET | `/healthz`, `/readyz`, `/metrics` | Probes and metrics |

Example:

```bash
curl -X POST http://localhost:8000/api/v1/devices/lab1/updates \
  -H "Content-Type: application/json" \
  -d '{"versions": {"OS": "15.3"}, "branch": "main", "commit_id": "a3f9c12"}'
```

Errors always look like this:

```json
{"error": "validation_error", "message": "OS 'abc' is not a valid version (expected digits and dots, e.g. 11.3.30)", "status": 400}
```

---

## Run locally

Requires Python 3.12.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements-dev.txt

$env:SECRET_KEY = "dev-only-key"       # required - the app refuses to start without it
$env:DATA_DIR   = "$PWD\data"          # where the CSV files go (git-ignored)
python wsgi.py                         # http://localhost:8000
```

| Variable | Default | Purpose |
|---|---|---|
| `SECRET_KEY` | - (required) | Flask session signing key |
| `DATA_DIR` | `/data` | Folder for the per-device CSV files |
| `APP_VERSION` | `dev` | Shown in `/healthz`; set to the commit SHA at build time |
| `LOG_LEVEL` | `INFO` | Logging level |
| `DEVICES` | `lab1..lab10` | Comma-separated device list |
| `MASTER_OS` / `_BE` / `_DB` / `_FW` | `15.2` / `11.3.30` / `12.0` / `3.6.0` | Master versions |

## Tests

Three suites in one codebase, selected with pytest markers:

| Suite | Command | What it covers | When it runs |
|---|---|---|---|
| **Sanity** | `python -m pytest -m sanity` | App starts, probes, all pages, one full update round-trip | Every PR and every merge |
| **Regression** | `python -m pytest -m regression` | Version edge cases, validation (400/404/405/503), upgrade/downgrade/no-change, history filters, persistence across restarts, storage failures, metrics | Nightly at 00:00 Israel time + on demand |
| **E2E** | `BASE_URL=http://... python -m pytest -m e2e` | The deployed app through nginx: probes, UI, static files, a real update | After every deploy |

```powershell
python -m pytest -q          # sanity + regression (e2e skips itself without BASE_URL)
python -m flake8 .           # lint - same rules as CI
```

Every test gets its own temporary data folder, so tests are independent and can run in any order. Coverage is ~96%.

## Docker

```powershell
docker build --build-arg APP_VERSION=local -t sw-update:local .
docker run -d -p 8080:8000 -e SECRET_KEY=dev-only-key -v sw-data:/data sw-update:local
```

- **Multi-stage**: dependencies are installed in a builder stage; only the finished venv is copied to the runtime image (~50 MB compressed).
- **`python:3.12-slim`** base, **non-root user** (UID 10001), code owned by root and read-only, only `/data` writable.
- **gunicorn** (1 worker, 4 threads) instead of the Flask dev server; Docker `HEALTHCHECK` on `/healthz`.

## CI/CD (GitHub Actions)

| Trigger | Workflow | Jobs |
|---|---|---|
| Pull request to `main` | `ci.yml` | flake8 → sanity → Docker build (no push) |
| Push / merge to `main` | `ci.yml` | flake8 → sanity → build & push `tareqelya12/sw-update:<sha>` → deploy to Minikube → E2E → verify `/healthz` reports the new SHA |
| Every night 00:00 (Asia/Jerusalem), or manual | `nightly-regression.yml` | flake8 → sanity + regression with coverage → summary table + reports |

- Images are tagged with the **short commit SHA** (immutable) plus `latest`.
- Credentials (`DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`, `APP_SECRET_KEY`) are **GitHub Secrets** - never in the code.
- The deploy job runs on a **self-hosted runner pod inside Minikube** whose ServiceAccount may only manage the `sw-update` namespace (see the devops repo).

## Project layout

```
app/                 Flask application (layers described above)
  templates/         Jinja2 HTML templates
  static/            Images
tests/
  test_sanity.py
  test_regression_versions.py
  test_regression_api.py
  e2e/test_e2e.py
.github/workflows/   ci.yml, nightly-regression.yml
Dockerfile, .dockerignore
requirements.txt     runtime dependencies
requirements-dev.txt + test and lint tools
```
