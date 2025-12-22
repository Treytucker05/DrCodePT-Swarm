"""Tests for execution profiles."""

import pytest
from agent.autonomous.profiles import (
    get_profile,
    list_profiles,
    FAST_PROFILE,
    DEEP_PROFILE,
    AUDIT_PROFILE,
)


def test_fast_profile_has_limited_budgets():
    """Test that fast profile has limited budgets."""
    profile = get_profile("fast")
    assert profile.max_steps == 20
    assert profile.timeout_seconds == 300
    assert profile.max_files_to_read == 50
    assert not profile.enable_code_execution


def test_deep_profile_has_moderate_budgets():
    """Test that deep profile has moderate budgets."""
    profile = get_profile("deep")
    assert profile.max_steps == 50
    assert profile.timeout_seconds == 1800
    assert profile.max_files_to_read == 200
    assert profile.enable_code_execution


def test_audit_profile_has_full_budgets():
    """Test that audit profile has full budgets."""
    profile = get_profile("audit")
    assert profile.max_steps == 100
    assert profile.timeout_seconds == 3600
    assert profile.max_files_to_read == 500
    assert profile.enable_code_execution


def test_get_profile_invalid_name():
    """Test that invalid profile name raises error."""
    with pytest.raises(ValueError):
        get_profile("invalid")


def test_list_profiles():
    """Test listing all profiles."""
    profiles = list_profiles()
    assert "fast" in profiles
    assert "deep" in profiles
    assert "audit" in profiles
    assert len(profiles) == 3


def test_profile_checkpoint_intervals():
    """Test that checkpoint intervals differ by profile."""
    fast = get_profile("fast")
    deep = get_profile("deep")
    audit = get_profile("audit")

    assert fast.checkpoint_interval == 10
    assert deep.checkpoint_interval == 5
    assert audit.checkpoint_interval == 1
