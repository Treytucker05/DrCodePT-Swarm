"""Tests for repository scanner."""

import pytest
import tempfile
from pathlib import Path
from agent.autonomous.tools.repo_scanner import RepoScanner, FileInfo


def test_repo_scanner_initialization():
    """Test RepoScanner initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        scanner = RepoScanner(Path(tmpdir), max_files=100, max_bytes=1_000_000)
        assert scanner.max_files == 100
        assert scanner.max_bytes == 1_000_000


def test_repo_scanner_identifies_file_types():
    """Test that scanner identifies file types correctly."""
    scanner = RepoScanner(Path("."))

    assert scanner._get_file_type(Path("test.py")) == "python"
    assert scanner._get_file_type(Path("README.md")) == "markdown"
    assert scanner._get_file_type(Path("config.json")) == "config"


def test_repo_scanner_identifies_key_files():
    """Test that scanner identifies key files."""
    scanner = RepoScanner(Path("."))

    is_key, reason = scanner._is_key_file(Path("README.md"))
    assert is_key
    assert reason is not None


def test_repo_scanner_respects_budgets():
    """Test that scanner respects file and byte budgets."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create test files
        for i in range(10):
            (tmpdir / f"file_{i}.txt").write_text("x" * 1000)

        scanner = RepoScanner(tmpdir, max_files=5, max_bytes=3000)
        index, _ = scanner.scan()

        assert len(index.files) <= 5
        assert index.total_bytes <= 3000


def test_repo_scanner_produces_index_and_map():
    """Test that scanner produces both index and map."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create test files
        (tmpdir / "README.md").write_text("# Test")
        (tmpdir / "setup.py").write_text("# Setup")
        (tmpdir / "test.py").write_text("# Test")

        scanner = RepoScanner(tmpdir)
        index, map_obj = scanner.scan()

        assert len(index.files) > 0
        assert len(map_obj.key_files) > 0
