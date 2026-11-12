"""Application configuration, read from environment variables.

Nothing secret is hardcoded here: SECRET_KEY must come from the environment
(a Kubernetes Secret in the cluster, a local .env file during development).
"""
import os


def _csv_env(name, default):
    raw = os.environ.get(name)
    if not raw:
        return list(default)
    return [item.strip() for item in raw.split(",") if item.strip()]


class Config:
    # Where per-device CSV files live. In Kubernetes this is a PVC mount.
    DATA_DIR = os.environ.get("DATA_DIR", "/data")

    # Flask session signing key (used by flash messages). Must be set in prod.
    SECRET_KEY = os.environ.get("SECRET_KEY")

    APP_VERSION = os.environ.get("APP_VERSION", "dev")
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

    DEVICES = _csv_env("DEVICES", [f"lab{i}" for i in range(1, 11)])

    # The "golden" versions every device is expected to run.
    # Also used as the starting point for a device seen for the first time.
    MASTER_VERSIONS = {
        "OS": os.environ.get("MASTER_OS", "15.2"),
        "BE": os.environ.get("MASTER_BE", "11.3.30"),
        "DB": os.environ.get("MASTER_DB", "12.0"),
        "FW": os.environ.get("MASTER_FW", "3.6.0"),
    }

    TESTING = False


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "test-only-key"
