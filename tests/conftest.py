"""Shared fixtures. Every test gets a brand-new app with its own empty data folder,
so tests never depend on each other or on leftovers from a previous run."""
import pytest

from app import create_app
from app.config import TestConfig


@pytest.fixture
def data_dir(tmp_path):
    return tmp_path / "data"


@pytest.fixture
def app(data_dir):
    return create_app(TestConfig, DATA_DIR=str(data_dir))


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def update(client):
    """Helper: POST an update through the API and return the response."""
    def _update(device, versions, **extra):
        return client.post(f"/api/v1/devices/{device}/updates", json={"versions": versions, **extra})
    return _update
