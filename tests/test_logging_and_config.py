from __future__ import annotations

import logging

import pytest

from agent.autonomous.config import RunnerConfig
from agent.autonomous.exceptions import ConfigurationError
from agent.autonomous.logging_config import configure_logging
from agent.config.profile import ProfileConfig


def test_logging_creates_agent_log(tmp_path) -> None:
    root = logging.getLogger()
    old_handlers = list(root.handlers)
    for handler in old_handlers:
        root.removeHandler(handler)
    try:
        configure_logging(tmp_path)
        assert (tmp_path / "agent.log").is_file()
    finally:
        for handler in list(root.handlers):
            root.removeHandler(handler)
        for handler in old_handlers:
            root.addHandler(handler)


def test_runner_config_validation() -> None:
    with pytest.raises(ConfigurationError):
        RunnerConfig(max_steps=0)


def test_profile_config_validation() -> None:
    with pytest.raises(ConfigurationError):
        ProfileConfig(
            name="fast",
            workers=0,
            plan_timeout_s=10,
            plan_retry_timeout_s=5,
            heartbeat_s=1,
            max_files_to_read=1,
            max_total_bytes_to_read=1,
            max_glob_results=1,
            max_web_sources=1,
            allow_interactive=False,
            stage_checkpoints=True,
        )
