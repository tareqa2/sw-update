"""Regression suite, part 1: version parsing and comparison rules (pure logic, no web)."""
import pytest

from app.errors import ValidationError
from app.versions import (DOWNGRADE, NO_CHANGE, UPGRADE, compare_version_strings, plan_actions,
                          validate_version)

pytestmark = pytest.mark.regression


@pytest.mark.parametrize("v1, v2, expected", [
    ("1.0", "1.0", 0),
    ("1.0", "1.0.0", 0),          # missing parts count as zero
    ("1.0.0.0", "1", 0),
    ("1.2", "1.10", -1),          # numeric, not alphabetical: 2 < 10
    ("1.10", "1.9", 1),
    ("10.0.19042", "10.0.19542", -1),
    ("2", "1.999", 1),
    ("15.3", "15.2", 1),
    ("0.0.1", "0.0.0", 1),
])
def test_compare_version_strings(v1, v2, expected):
    assert compare_version_strings(v1, v2) == expected


@pytest.mark.parametrize("value", ["15.2", "1", "11.3.30", "10.0.19042.1", "  12.0  "])
def test_valid_versions_accepted(value):
    assert validate_version(value) == value.strip()


@pytest.mark.parametrize("value", [
    "", "   ", "abc", "1.", ".1", "1..2", "1.2.3.4.5", "v1.2", "1.2-beta", "-1", "1,2", "1" * 40, None, 15,
])
def test_invalid_versions_rejected(value):
    with pytest.raises(ValidationError):
        validate_version(value)


def test_plan_actions_all_three_outcomes():
    installed = {"OS": "15.2", "DB": "12.0", "FW": "3.6.0"}
    desired = {"OS": "15.3", "DB": "11.9", "FW": "3.6.0"}
    assert plan_actions(installed, desired) == {"OS": UPGRADE, "DB": DOWNGRADE, "FW": NO_CHANGE}


def test_plan_actions_missing_component_means_no_change():
    assert plan_actions({"OS": "15.2", "DB": "12.0"}, {"OS": "15.3"}) == {"OS": UPGRADE, "DB": NO_CHANGE}


def test_plan_actions_rejects_unknown_component():
    with pytest.raises(ValidationError):
        plan_actions({"OS": "15.2"}, {"GPU": "1.0"})
