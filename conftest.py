import os
import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests (skipped by default).",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "integration: marks tests that require external services or credentials",
    )
    if not config.getoption("--run-integration"):
        os.environ.setdefault("TREYS_AGENT_DISABLE_MCP", "1")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--run-integration"):
        return
    skip_integration = pytest.mark.skip(
        reason="integration test skipped (use --run-integration to enable)"
    )
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)
