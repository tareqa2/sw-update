# ---------- Stage 1: builder ----------
# Installs Python dependencies into a virtualenv. Anything needed only to
# *install* packages stays in this stage and never reaches the final image.
FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# requirements.txt is copied alone first: this layer is cached and only
# rebuilt when dependencies change, not on every code change.
COPY requirements.txt /tmp/requirements.txt
RUN python -m venv /opt/venv \
 && /opt/venv/bin/pip install -r /tmp/requirements.txt


# ---------- Stage 2: runtime ----------
FROM python:3.12-slim AS runtime

ARG APP_VERSION=dev
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    DATA_DIR=/data \
    APP_VERSION=${APP_VERSION}

# Unprivileged user with a fixed UID (Kubernetes securityContext refers to it).
RUN groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app \
 && mkdir /data && chown app:app /data

WORKDIR /srv
COPY --from=builder /opt/venv /opt/venv
# Code is owned by root and read-only for the app user: a compromised
# process can't modify its own code. Only /data is writable.
COPY app/ ./app/
COPY wsgi.py .

USER 10001
EXPOSE 8000

# Docker-level health check (Kubernetes uses its own probes instead).
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2).status == 200 else 1)"]

# One worker + threads: metrics live in one process, CSV writes stay serialized.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "4", \
     "--access-logfile", "-", "--error-logfile", "-", "wsgi:app"]
