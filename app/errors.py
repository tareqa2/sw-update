"""Domain exceptions and JSON error handlers for the API."""
import logging

from flask import jsonify, request
from werkzeug.exceptions import HTTPException

log = logging.getLogger(__name__)


class AppError(Exception):
    status_code = 500
    error = "internal_error"

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class ValidationError(AppError):
    status_code = 400
    error = "validation_error"


class NotFoundError(AppError):
    status_code = 404
    error = "not_found"


class StorageError(AppError):
    status_code = 503
    error = "storage_unavailable"


def _wants_json():
    return request.path.startswith("/api/")


def _json_error(status, error, message):
    return jsonify({"error": error, "message": message, "status": status}), status


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(exc):
        if exc.status_code >= 500:
            log.error("%s: %s", exc.error, exc.message)
        if _wants_json():
            return _json_error(exc.status_code, exc.error, exc.message)
        return exc.message, exc.status_code

    @app.errorhandler(HTTPException)
    def handle_http_error(exc):
        if _wants_json():
            return _json_error(exc.code, exc.name.lower().replace(" ", "_"), exc.description)
        return exc

    @app.errorhandler(Exception)
    def handle_unexpected(exc):
        log.exception("Unhandled error on %s %s", request.method, request.path)
        if _wants_json():
            return _json_error(500, "internal_error", "unexpected server error")
        return "Internal server error", 500
