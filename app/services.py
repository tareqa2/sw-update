"""Business logic. The API and the HTML views both call this layer,
so validation and update rules live in exactly one place."""
import re

from . import versions
from .errors import NotFoundError, ValidationError

BRANCHES = {"manual", "master", "main"}
COMMIT_RE = re.compile(r"^[0-9a-fA-F]{7,40}$")
BRANCH_NAME_RE = re.compile(r"^[A-Za-z0-9._/-]{1,64}$")
ACTION_FILTERS = {versions.UPGRADE, versions.DOWNGRADE, versions.NO_CHANGE}


class VersionService:
    def __init__(self, store, devices, master_versions, metrics=None):
        self.store = store
        self.devices = list(devices)
        self.master = dict(master_versions)
        self.metrics = metrics

    # ---- validation helpers -------------------------------------------------
    def _check_device(self, device):
        if device not in self.devices:
            raise NotFoundError(f"device '{device}' not found")

    @staticmethod
    def _clean_source(branch, commit_id):
        branch = (branch or "manual").strip()
        commit_id = (commit_id or "").strip()
        if branch not in BRANCHES and not BRANCH_NAME_RE.match(branch):
            raise ValidationError(f"invalid branch '{branch}'")
        if branch == "manual":
            commit_id = ""
        elif commit_id and not COMMIT_RE.match(commit_id):
            raise ValidationError("commit_id must be a 7-40 character hex git SHA")
        return branch, commit_id

    def _clean_desired(self, desired):
        if not isinstance(desired, dict) or not desired:
            raise ValidationError("'versions' must be a non-empty object, e.g. {\"OS\": \"15.3\"}")
        cleaned = {}
        for component, value in desired.items():
            if component not in self.master:
                raise ValidationError(f"unknown component '{component}'")
            cleaned[component] = versions.validate_version(value, field=component)
        return cleaned

    # ---- queries ------------------------------------------------------------
    def list_devices(self):
        result = []
        for device in self.devices:
            installed = self.store.get_versions(device, self.master)
            outdated = [c for c, v in installed.items()
                        if versions.compare_version_strings(v, self.master.get(c, v)) != 0]
            result.append({"id": device, "in_sync": not outdated, "outdated_components": outdated})
        return result

    def get_device(self, device):
        self._check_device(device)
        details = self.store.get_details(device, self.master)
        for component, info in details.items():
            master = self.master.get(component)
            info["master"] = master
            info["in_sync"] = master is not None and versions.compare_version_strings(info["version"], master) == 0
        return {"id": device, "components": details}

    def get_history(self, device, component=None, action=None, limit=None):
        self._check_device(device)
        if component and component not in self.master:
            raise ValidationError(f"unknown component '{component}'")
        if action and action not in ACTION_FILTERS:
            raise ValidationError(f"action must be one of {sorted(ACTION_FILTERS)}")
        if limit is not None and (limit < 1 or limit > 1000):
            raise ValidationError("limit must be between 1 and 1000")

        records = self.store.get_history(device)
        if component:
            records = [r for r in records if r["Component"] == component]
        if action:
            records = [r for r in records if r["Action"] == action]
        records = list(reversed(records))  # newest first
        return records[:limit] if limit else records

    # ---- commands -----------------------------------------------------------
    def plan_update(self, device, desired):
        """Dry run: what would happen, without changing anything."""
        self._check_device(device)
        desired = self._clean_desired(desired)
        installed = self.store.get_versions(device, self.master)
        full_desired = {c: desired.get(c, v) for c, v in installed.items()}
        actions = versions.plan_actions(installed, full_desired)
        return installed, full_desired, actions

    @staticmethod
    def _source_kind(branch):
        """Low-cardinality label for metrics: free-form side-branch names collapse to 'side'."""
        return branch if branch in BRANCHES else "side"

    def apply_update(self, device, desired, branch="manual", commit_id="", channel="api"):
        branch, commit_id = self._clean_source(branch, commit_id)
        installed, full_desired, actions = self.plan_update(device, desired)
        self.store.apply_update(device, installed, full_desired, actions, branch, commit_id)
        if self.metrics:
            # Count only the components the caller asked about; untouched ones are not "no change" requests.
            for component in desired:
                self.metrics.record_update(device, component, actions[component])
            self.metrics.record_operation(device, channel, self._source_kind(branch))
        return {
            "device": device,
            "branch": branch,
            "commit_id": commit_id or None,
            "changes": {
                c: {"from": installed[c], "to": full_desired[c], "action": actions[c]}
                for c in installed
            },
        }
