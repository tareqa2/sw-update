"""Prometheus metrics: HTTP traffic plus app-specific business metrics.

Gunicorn runs one worker with several threads, so the default
prometheus_client registry is safe to use (no multiprocess mode needed).
"""
import time

from flask import Blueprint, Response, current_app, g, request
from prometheus_client import (CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Gauge,
                               Histogram, generate_latest)


class Metrics:
    def __init__(self):
        # A private registry per app instance keeps tests isolated from each other.
        self.registry = CollectorRegistry()
        self.http_requests = Counter(
            "swupdate_http_requests_total", "HTTP requests",
            ["method", "endpoint", "status"], registry=self.registry)
        self.http_latency = Histogram(
            "swupdate_http_request_duration_seconds", "HTTP request latency",
            ["method", "endpoint"], registry=self.registry)
        self.updates = Counter(
            "swupdate_component_updates_total", "Component update actions applied",
            ["device", "component", "action"], registry=self.registry)
        self.devices_out_of_sync = Gauge(
            "swupdate_devices_out_of_sync", "Devices with at least one component off master",
            registry=self.registry)
        self.app_info = Gauge(
            "swupdate_app_info", "Build information", ["version"], registry=self.registry)

    def record_update(self, device, component, action):
        self.updates.labels(device, component, action).inc()

    def init_app(self, app):
        self.app_info.labels(app.config["APP_VERSION"]).set(1)

        @app.before_request
        def _start_timer():
            g._start = time.perf_counter()

        @app.after_request
        def _record(response):
            endpoint = request.url_rule.rule if request.url_rule else "unmatched"
            if endpoint != "/metrics":
                elapsed = time.perf_counter() - g.get("_start", time.perf_counter())
                self.http_latency.labels(request.method, endpoint).observe(elapsed)
                self.http_requests.labels(request.method, endpoint, response.status_code).inc()
            return response


bp = Blueprint("metrics", __name__)


@bp.get("/metrics")
def metrics_endpoint():
    metrics = current_app.extensions["metrics"]
    service = current_app.extensions["service"]
    try:
        out_of_sync = sum(1 for d in service.list_devices() if not d["in_sync"])
        metrics.devices_out_of_sync.set(out_of_sync)
    except Exception:  # never let a storage hiccup break scraping
        current_app.logger.warning("could not compute devices_out_of_sync", exc_info=True)
    return Response(generate_latest(metrics.registry), mimetype=CONTENT_TYPE_LATEST)
