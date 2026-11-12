"""Server-rendered UI (the original sw-update pages), backed by the same service layer as the API."""
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from .errors import ValidationError

bp = Blueprint("web", __name__)


def _service():
    return current_app.extensions["service"]


def _device():
    device = request.values.get("device") or _service().devices[0]
    _service()._check_device(device)  # raises NotFoundError -> 404
    return device


def _ctx(device, **extra):
    return dict(device=device, devices=_service().devices, master=_service().master, **extra)


@bp.get("/")
def index():
    device = _device()
    details = _service().get_device(device)["components"]
    return render_template("index.html", details=details, **_ctx(device))


@bp.route("/update", methods=["GET", "POST"])
def update():
    device = _device()
    service = _service()
    installed = service.store.get_versions(device, service.master)

    if request.method == "GET":
        return render_template("update.html", installed=installed, desired={}, actions={},
                               confirm=False, branch="manual", commit_id="", **_ctx(device))

    branch = request.form.get("branch", "manual")
    if branch == "side":
        branch = request.form.get("branch_name", "").strip() or "side"
    commit_id = request.form.get("commit_id", "").strip()
    desired = {c: request.form.get(c, "").strip() for c in installed}
    desired = {c: v for c, v in desired.items() if v}

    try:
        if not desired:
            raise ValidationError("enter at least one target version")
        if "confirm" in request.form:
            service.apply_update(device, desired, branch=branch, commit_id=commit_id)
            flash(f"{device.upper()} updated", "success")
            return redirect(url_for("web.index", device=device))
        installed, full_desired, actions = service.plan_update(device, desired)
        service._clean_source(branch, commit_id)
    except ValidationError as exc:
        flash(exc.message, "error")
        return render_template("update.html", installed=installed, desired={}, actions={},
                               confirm=False, branch="manual", commit_id="", **_ctx(device)), 400

    return render_template("update.html", installed=installed, desired=full_desired, actions=actions,
                           confirm=True, branch=branch, commit_id=commit_id, **_ctx(device))


@bp.get("/history")
def history():
    device = _device()
    # The template reverses the list itself, so pass oldest-first.
    records = list(reversed(_service().get_history(device)))
    return render_template("history.html", records=records, **_ctx(device))
