"""Regression suite, part 2: API behaviour, validation, persistence, UI flow, storage edge cases.

Runs nightly (and on demand). Every bug found gets a test here so it can't come back.
"""
import pytest

import app.storage as storage_module
from app import create_app
from app.config import TestConfig

pytestmark = pytest.mark.regression


# ---- input validation -> 4xx, never 500 -------------------------------------
@pytest.mark.parametrize("body, message_part", [
    ({"versions": {"OS": "abc"}}, "not a valid version"),
    ({"versions": {"GPU": "1.0"}}, "unknown component"),
    ({"versions": {}}, "non-empty object"),
    ({"versions": "15.3"}, "non-empty object"),
    ({}, "non-empty object"),
    ({"versions": {"OS": "15.3"}, "branch": "master", "commit_id": "xyz"}, "commit_id"),
    ({"versions": {"OS": "15.3"}, "branch": "bad branch name!"}, "invalid branch"),
])
def test_update_validation_errors(client, body, message_part):
    r = client.post("/api/v1/devices/lab1/updates", json=body)
    assert r.status_code == 400
    payload = r.get_json()
    assert payload["error"] == "validation_error"
    assert message_part in payload["message"]


def test_non_json_body_is_rejected(client):
    r = client.post("/api/v1/devices/lab1/updates", data="OS=15.3", content_type="text/plain")
    assert r.status_code == 400
    assert r.get_json()["error"] == "validation_error"


@pytest.mark.parametrize("path", [
    "/api/v1/devices/lab99",
    "/api/v1/devices/lab99/history",
])
def test_unknown_device_is_404(client, path):
    r = client.get(path)
    assert r.status_code == 404
    assert r.get_json()["error"] == "not_found"


def test_unknown_api_route_returns_json_404(client):
    r = client.get("/api/v1/nope")
    assert r.status_code == 404
    assert r.is_json


def test_wrong_method_returns_json_405(client):
    r = client.delete("/api/v1/devices/lab1")
    assert r.status_code == 405
    assert r.is_json


def test_failed_validation_changes_nothing(client, update):
    before = client.get("/api/v1/devices/lab1").get_json()
    update("lab1", {"OS": "15.3", "DB": "not-a-version"})
    after = client.get("/api/v1/devices/lab1").get_json()
    assert before["components"]["OS"]["version"] == after["components"]["OS"]["version"] == "15.2"
    assert client.get("/api/v1/devices/lab1/history").get_json()["count"] == 0


# ---- update behaviour ------------------------------------------------------
def test_upgrade_downgrade_and_no_change_in_one_update(client, update):
    r = update("lab2", {"OS": "16.0", "DB": "11.0", "FW": "3.6.0"}, branch="master", commit_id="a3f9c12")
    changes = r.get_json()["changes"]
    assert changes["OS"] == {"from": "15.2", "to": "16.0", "action": "upgrade"}
    assert changes["DB"] == {"from": "12.0", "to": "11.0", "action": "downgrade"}
    assert changes["FW"]["action"] == "no_change"
    assert changes["BE"]["action"] == "no_change"  # not mentioned -> untouched

    comps = client.get("/api/v1/devices/lab2").get_json()["components"]
    assert comps["OS"]["version"] == "16.0" and comps["OS"]["previous"] == "15.2"
    assert comps["OS"]["in_sync"] is False
    assert comps["FW"]["in_sync"] is True


def test_plan_is_a_dry_run(client):
    r = client.post("/api/v1/devices/lab3/plan", json={"versions": {"OS": "16.0"}})
    assert r.status_code == 200
    assert r.get_json()["changes"]["OS"]["action"] == "upgrade"
    assert client.get("/api/v1/devices/lab3").get_json()["components"]["OS"]["version"] == "15.2"


def test_manual_branch_drops_commit_id(client, update):
    r = update("lab1", {"OS": "15.3"}, branch="manual", commit_id="a3f9c12")
    assert r.get_json()["commit_id"] is None


def test_devices_are_isolated(client, update):
    update("lab1", {"OS": "16.0"})
    assert client.get("/api/v1/devices/lab2").get_json()["components"]["OS"]["version"] == "15.2"


def test_device_list_reports_out_of_sync(client, update):
    update("lab4", {"BE": "11.4.0"})
    devices = {d["id"]: d for d in client.get("/api/v1/devices").get_json()}
    assert devices["lab4"]["in_sync"] is False
    assert devices["lab4"]["outdated_components"] == ["BE"]
    assert devices["lab5"]["in_sync"] is True


# ---- history ------------------------------------------------------------------
def test_history_newest_first_and_filters(client, update):
    update("lab1", {"OS": "15.3"})
    update("lab1", {"OS": "15.1"})
    hist = client.get("/api/v1/devices/lab1/history?component=OS").get_json()["records"]
    assert [r["Action"] for r in hist] == ["downgrade", "upgrade"]

    downgrades = client.get("/api/v1/devices/lab1/history?action=downgrade").get_json()
    assert downgrades["count"] == 1

    limited = client.get("/api/v1/devices/lab1/history?limit=3").get_json()
    assert limited["count"] == 3


@pytest.mark.parametrize("query", ["limit=0", "limit=abc", "limit=5000", "action=explode", "component=GPU"])
def test_history_bad_query_params(client, query):
    r = client.get(f"/api/v1/devices/lab1/history?{query}")
    assert r.status_code == 400


# ---- persistence --------------------------------------------------------------
def test_data_survives_app_restart(data_dir, update):
    """Simulates a pod restart: a brand-new app on the same volume must see old data."""
    update("lab6", {"OS": "16.1"})
    restarted = create_app(TestConfig, DATA_DIR=str(data_dir)).test_client()
    assert restarted.get("/api/v1/devices/lab6").get_json()["components"]["OS"]["version"] == "16.1"


def test_no_temp_files_left_behind(data_dir, update):
    update("lab1", {"OS": "15.3"})
    leftovers = [p.name for p in data_dir.iterdir() if p.name.startswith(".tmp-")]
    assert leftovers == []


def test_missing_data_dir_is_created_without_file_locking(tmp_path, monkeypatch):
    """Regression for the bug found on Windows: no fcntl -> data dir was never created -> 503."""
    monkeypatch.setattr(storage_module, "fcntl", None)
    data_dir = tmp_path / "does" / "not" / "exist"
    client = create_app(TestConfig, DATA_DIR=str(data_dir)).test_client()
    assert client.get("/api/v1/devices/lab1").status_code == 200
    assert (data_dir / "lab1_versions.csv").exists()


def test_readiness_fails_when_storage_unwritable(tmp_path):
    blocker = tmp_path / "not-a-dir"
    blocker.write_text("this is a file, so it can't be used as a directory")
    client = create_app(TestConfig, DATA_DIR=str(blocker)).test_client()
    assert client.get("/healthz").status_code == 200   # process alive...
    assert client.get("/readyz").status_code == 503    # ...but not ready for traffic
    r = client.get("/api/v1/devices/lab1")
    assert r.status_code == 503 and r.get_json()["error"] == "storage_unavailable"


# ---- UI flow ----------------------------------------------------------------------
def test_ui_update_flow_plan_then_confirm(client):
    plan = client.post("/update", data={"device": "lab7", "OS": "16.0", "branch": "manual"})
    assert plan.status_code == 200
    assert b"16.0" in plan.data

    confirm = client.post("/update", data={"device": "lab7", "OS": "16.0", "branch": "manual", "confirm": "1"})
    assert confirm.status_code == 302
    assert client.get("/api/v1/devices/lab7").get_json()["components"]["OS"]["version"] == "16.0"


def test_ui_rejects_invalid_version_without_crashing(client):
    r = client.post("/update", data={"device": "lab7", "OS": "banana", "branch": "manual", "confirm": "1"})
    assert r.status_code == 400
    assert b"not a valid version" in r.data


def test_ui_unknown_device_is_404(client):
    assert client.get("/?device=lab99").status_code == 404


def test_app_refuses_to_start_without_secret_key(data_dir):
    with pytest.raises(RuntimeError):
        create_app(TestConfig, DATA_DIR=str(data_dir), SECRET_KEY=None)


# ---- metrics ------------------------------------------------------------------------
def test_update_metrics_are_counted(client, update):
    update("lab8", {"OS": "16.0"})
    body = client.get("/metrics").get_data(as_text=True)
    assert 'swupdate_component_updates_total{action="upgrade",component="OS",device="lab8"} 1.0' in body
    assert "swupdate_devices_out_of_sync 1.0" in body
