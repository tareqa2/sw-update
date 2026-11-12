"""Sanity suite: "is the build alive and are the main paths working?"

Fast (a few seconds), so it gates every pull request and every merge.
If any of these fail, nothing else is worth running.
"""
import pytest

pytestmark = pytest.mark.sanity


def test_liveness(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"


def test_readiness(client):
    r = client.get("/readyz")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ready"


@pytest.mark.parametrize("path", ["/", "/update", "/history"])
def test_ui_pages_render(client, path):
    r = client.get(path)
    assert r.status_code == 200
    assert b"<html" in r.data


def test_list_devices(client):
    r = client.get("/api/v1/devices")
    assert r.status_code == 200
    assert len(r.get_json()) == 10


def test_master_versions(client):
    r = client.get("/api/v1/master")
    assert r.status_code == 200
    assert set(r.get_json()) == {"OS", "BE", "DB", "FW"}


def test_update_round_trip(client, update):
    """The core business flow, end to end inside the app: update -> read back -> history."""
    r = update("lab1", {"OS": "15.3"})
    assert r.status_code == 201
    assert r.get_json()["changes"]["OS"]["action"] == "upgrade"

    device = client.get("/api/v1/devices/lab1").get_json()
    assert device["components"]["OS"]["version"] == "15.3"

    history = client.get("/api/v1/devices/lab1/history").get_json()
    assert history["count"] == 4  # one row per component


def test_metrics_endpoint(client):
    r = client.get("/metrics")
    assert r.status_code == 200
    assert b"swupdate_http_requests_total" in r.data
