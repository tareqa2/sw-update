"""REST API - /api/v1. Every response is JSON, including errors."""
from flask import Blueprint, current_app, jsonify, request

from .errors import ValidationError

bp = Blueprint("api", __name__, url_prefix="/api/v1")


def _service():
    return current_app.extensions["service"]


def _json_body():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        raise ValidationError("request body must be a JSON object")
    return body


@bp.get("/master")
def get_master():
    return jsonify(_service().master)


@bp.get("/devices")
def list_devices():
    return jsonify(_service().list_devices())


@bp.get("/devices/<device>")
def get_device(device):
    return jsonify(_service().get_device(device))


@bp.post("/devices/<device>/plan")
def plan_update(device):
    body = _json_body()
    installed, desired, actions = _service().plan_update(device, body.get("versions"))
    return jsonify({
        "device": device,
        "changes": {c: {"from": installed[c], "to": desired[c], "action": actions[c]} for c in installed},
    })


@bp.post("/devices/<device>/updates")
def apply_update(device):
    body = _json_body()
    result = _service().apply_update(
        device, body.get("versions"), branch=body.get("branch", "manual"), commit_id=body.get("commit_id", ""))
    current_app.logger.info("update applied device=%s branch=%s", device, result["branch"])
    return jsonify(result), 201


@bp.get("/devices/<device>/history")
def get_history(device):
    limit = request.args.get("limit")
    if limit is not None:
        if not limit.isdigit():
            raise ValidationError("limit must be a positive integer")
        limit = int(limit)
    records = _service().get_history(
        device, component=request.args.get("component"), action=request.args.get("action"), limit=limit)
    return jsonify({"device": device, "count": len(records), "records": records})
