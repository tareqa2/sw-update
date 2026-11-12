"""Application factory.

create_app() builds a fresh Flask app every time, which is what lets each
test run against its own temporary data directory.
"""
import logging
import sys

from flask import Flask

from . import api, health, metrics, web
from .config import Config
from .errors import register_error_handlers
from .services import VersionService
from .storage import CsvStore


def _configure_logging(level):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)


def create_app(config_object=Config, **overrides):
    app = Flask(__name__)
    app.config.from_object(config_object)
    app.config.update(overrides)

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY environment variable is required")

    _configure_logging(app.config["LOG_LEVEL"])

    app_metrics = metrics.Metrics()
    app_metrics.init_app(app)
    store = CsvStore(app.config["DATA_DIR"])
    service = VersionService(store, app.config["DEVICES"], app.config["MASTER_VERSIONS"], app_metrics)

    app.extensions["metrics"] = app_metrics
    app.extensions["store"] = store
    app.extensions["service"] = service

    app.register_blueprint(health.bp)
    app.register_blueprint(metrics.bp)
    app.register_blueprint(api.bp)
    app.register_blueprint(web.bp)
    register_error_handlers(app)
    return app
