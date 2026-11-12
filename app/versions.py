"""Version string parsing and comparison - pure functions, no I/O.

Kept free of Flask and file access so it can be unit tested in isolation.
"""
import re

from .errors import ValidationError

# 1 to 4 numeric parts separated by dots, e.g. "15", "15.2", "11.3.30", "10.0.19042.1"
VERSION_RE = re.compile(r"^\d+(\.\d+){0,3}$")
MAX_VERSION_LENGTH = 32

UPGRADE = "upgrade"
DOWNGRADE = "downgrade"
NO_CHANGE = "no_change"


def validate_version(value, field="version"):
    """Return the cleaned version string or raise ValidationError."""
    if not isinstance(value, str):
        raise ValidationError(f"{field} must be a string")
    value = value.strip()
    if not value:
        raise ValidationError(f"{field} must not be empty")
    if len(value) > MAX_VERSION_LENGTH:
        raise ValidationError(f"{field} is too long (max {MAX_VERSION_LENGTH} chars)")
    if not VERSION_RE.match(value):
        raise ValidationError(
            f"{field} '{value}' is not a valid version (expected digits and dots, e.g. 11.3.30)"
        )
    return value


def compare_version_strings(v1, v2):
    """Compare two versions part by part. Returns 1 if v1 > v2, -1 if v1 < v2, 0 if equal.

    Missing parts count as 0, so "1.0" == "1.0.0".
    """
    p1 = [int(x) for x in validate_version(v1).split(".")]
    p2 = [int(x) for x in validate_version(v2).split(".")]
    length = max(len(p1), len(p2))
    p1 += [0] * (length - len(p1))
    p2 += [0] * (length - len(p2))
    if p1 > p2:
        return 1
    if p1 < p2:
        return -1
    return 0


def plan_actions(installed, desired):
    """For each installed component, decide upgrade / downgrade / no_change.

    Components not mentioned in `desired` are treated as no_change.
    Unknown components in `desired` are rejected.
    """
    unknown = set(desired) - set(installed)
    if unknown:
        raise ValidationError(f"unknown component(s): {', '.join(sorted(unknown))}")

    actions = {}
    for component, current in installed.items():
        target = desired.get(component, current)
        result = compare_version_strings(current, target)
        if result < 0:
            actions[component] = UPGRADE
        elif result > 0:
            actions[component] = DOWNGRADE
        else:
            actions[component] = NO_CHANGE
    return actions
