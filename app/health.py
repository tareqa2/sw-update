"""Liveness and readiness endpoints for Kubernetes probes.

/healthz  - liveness: the process is up and serving. No dependencies checked,
            so a slow disk never gets a healthy pod killed.
/readyz   - readiness: the data volume is mounted and writable. If not, the pod
            is taken out of the Service until it recovers.
"""
from flask import Blueprint, current_app, jsonify

bp = Blueprint("health", __name__)


@bp.get("/healthz")
def healthz():
    return jsonify(status="ok", version=current_app.config["APP_VERSION"])


@bp.get("/readyz")
def readyz():
    store = current_app.extensions["store"]
    if store.is_writable():
        return jsonify(status="ready")
    return jsonify(status="not_ready", reason="data directory is not writable"), 503
