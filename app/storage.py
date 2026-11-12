"""CSV-backed storage for device versions and update history.

One pair of files per device:
    <DATA_DIR>/<device>_versions.csv
    <DATA_DIR>/<device>_history.csv

Writes are atomic (write to a temp file, then os.replace) and serialized with
a file lock, so a crash mid-write never leaves a half-written CSV behind.
"""
import csv
import os
import tempfile
import threading
from contextlib import contextmanager
from datetime import datetime, timezone

from .errors import StorageError

try:  # POSIX file locking (Linux containers). Falls back to a thread lock on Windows.
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None

VERSION_HEADERS = ["Component", "CurrentVersion", "LastUpdateDate", "PreviousVersion", "UpdateStatus"]
HISTORY_HEADERS = ["Timestamp", "Component", "OldVersion", "NewVersion", "Action", "Branch", "CommitID"]

_thread_lock = threading.Lock()


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


class CsvStore:
    def __init__(self, data_dir):
        self.data_dir = data_dir

    # ---- paths -------------------------------------------------------------
    def _versions_file(self, device):
        return os.path.join(self.data_dir, f"{device}_versions.csv")

    def _history_file(self, device):
        return os.path.join(self.data_dir, f"{device}_history.csv")

    # ---- health ------------------------------------------------------------
    def is_writable(self):
        """Readiness check: the data directory exists and we can write to it."""
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=self.data_dir, prefix=".probe-"):
                pass
            return True
        except OSError:
            return False

    # ---- locking -----------------------------------------------------------
    @contextmanager
    def _locked(self):
        with _thread_lock:
            # Create the data dir on every platform before touching files in it.
            os.makedirs(self.data_dir, exist_ok=True)
            if fcntl is None:
                yield
                return
            with open(os.path.join(self.data_dir, ".lock"), "w") as lock_file:
                fcntl.flock(lock_file, fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(lock_file, fcntl.LOCK_UN)

    def _atomic_write(self, path, headers, rows):
        directory = os.path.dirname(path)
        fd, tmp_path = tempfile.mkstemp(dir=directory, prefix=".tmp-", suffix=".csv")
        try:
            with os.fdopen(fd, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(rows)
            os.replace(tmp_path, path)
        except BaseException:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise

    # ---- versions ----------------------------------------------------------
    def get_details(self, device, defaults):
        """Return {component: {version, previous, status, updated_at}}.

        A device seen for the first time is initialised with `defaults`.
        """
        try:
            with self._locked():
                path = self._versions_file(device)
                if not os.path.exists(path):
                    now = _now()
                    rows = [
                        {"Component": c, "CurrentVersion": v, "LastUpdateDate": now,
                         "PreviousVersion": "", "UpdateStatus": "initial"}
                        for c, v in defaults.items()
                    ]
                    self._atomic_write(path, VERSION_HEADERS, rows)
                with open(path, newline="") as f:
                    rows = list(csv.DictReader(f))
        except OSError as exc:
            raise StorageError(f"cannot read versions for {device}: {exc}") from exc

        return {
            r["Component"]: {
                "version": r["CurrentVersion"],
                "previous": r.get("PreviousVersion") or None,
                "status": r.get("UpdateStatus", "initial"),
                "updated_at": r.get("LastUpdateDate"),
            }
            for r in rows
        }

    def get_versions(self, device, defaults):
        return {c: d["version"] for c, d in self.get_details(device, defaults).items()}

    def apply_update(self, device, current, desired, actions, branch, commit_id):
        """Persist new versions and append one history row per component, in one locked step."""
        now = _now()
        try:
            with self._locked():
                version_rows = []
                for component, old in current.items():
                    changed = actions[component] != "no_change"
                    version_rows.append({
                        "Component": component,
                        "CurrentVersion": desired[component] if changed else old,
                        "LastUpdateDate": now,
                        "PreviousVersion": old if changed else "",
                        "UpdateStatus": "updated" if changed else "unchanged",
                    })
                self._atomic_write(self._versions_file(device), VERSION_HEADERS, version_rows)

                history_path = self._history_file(device)
                new_file = not os.path.exists(history_path)
                with open(history_path, "a", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=HISTORY_HEADERS)
                    if new_file:
                        writer.writeheader()
                    for component, old in current.items():
                        writer.writerow({
                            "Timestamp": now, "Component": component, "OldVersion": old,
                            "NewVersion": desired[component], "Action": actions[component],
                            "Branch": branch, "CommitID": commit_id,
                        })
        except OSError as exc:
            raise StorageError(f"cannot save update for {device}: {exc}") from exc

    # ---- history -----------------------------------------------------------
    def get_history(self, device):
        path = self._history_file(device)
        if not os.path.exists(path):
            return []
        try:
            with open(path, newline="") as f:
                return list(csv.DictReader(f))
        except OSError as exc:
            raise StorageError(f"cannot read history for {device}: {exc}") from exc
