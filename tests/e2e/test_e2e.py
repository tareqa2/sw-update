"""E2E suite: runs against a *deployed* app (through nginx), not the Flask test client.

    $env:BASE_URL = "http://127.0.0.1:30080"; pytest -m e2e

Proves the Kubernetes wiring works: nginx -> Service -> Flask pod -> volume.
Skipped automatically when BASE_URL is not set.
"""
import os
import uuid

import pytest
import requests

BASE_URL = os.environ.get("BASE_URL", "").rstrip("/")
TIMEOUT = 10

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(not BASE_URL, reason="BASE_URL not set - no deployed app to test"),
]

# Use the last device so e2e runs don't disturb the devices people look at in demos.
DEVICE = "lab10"


def get(path):
    return requests.get(f"{BASE_URL}{path}", timeout=TIMEOUT)


def test_health_through_nginx():
    r = get("/healthz")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_ready_through_nginx():
    assert get("/readyz").status_code == 200


def test_static_files_served_by_nginx():
    r = get("/static/OS.jpg")
    assert r.status_code == 200
    assert r.headers["Content-Type"].startswith("image/")


@pytest.mark.parametrize("path", ["/", "/update", "/history"])
def test_ui_pages(path):
    assert get(path).status_code == 200


def test_api_update_flow_on_live_cluster():
    current = get(f"/api/v1/devices/{DEVICE}").json()["components"]["FW"]["version"]
    major, minor, patch = (current.split(".") + ["0", "0"])[:3]
    target = f"{major}.{minor}.{int(patch) + 1}"
    commit = uuid.uuid4().hex[:7]

    r = requests.post(f"{BASE_URL}/api/v1/devices/{DEVICE}/updates", timeout=TIMEOUT,
                      json={"versions": {"FW": target}, "branch": "main", "commit_id": commit})
    assert r.status_code == 201
    assert r.json()["changes"]["FW"]["action"] == "upgrade"

    assert get(f"/api/v1/devices/{DEVICE}").json()["components"]["FW"]["version"] == target
    latest = get(f"/api/v1/devices/{DEVICE}/history?component=FW&limit=1").json()["records"][0]
    assert latest["CommitID"] == commit


def test_validation_through_nginx():
    r = requests.post(f"{BASE_URL}/api/v1/devices/{DEVICE}/updates", json={"versions": {"FW": "x"}},
                      timeout=TIMEOUT)
    assert r.status_code == 400
