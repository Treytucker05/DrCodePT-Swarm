"""Tests for filesystem sandbox."""

import pytest
import tempfile
from pathlib import Path
from agent.autonomous.security.filesystem_sandbox import FilesystemSandbox


@pytest.fixture
def temp_dirs():
    """Create temporary directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        allowed = tmpdir / "allowed"
        allowed.mkdir()
        forbidden = tmpdir / "forbidden"
        forbidden.mkdir()
        
        yield allowed, forbidden


def test_filesystem_sandbox_initialization(temp_dirs):
    """Test FilesystemSandbox initialization."""
    allowed, _ = temp_dirs
    sandbox = FilesystemSandbox([allowed])
    
    assert len(sandbox.allowed_dirs) == 1


def test_is_path_allowed(temp_dirs):
    """Test checking if path is allowed."""
    allowed, forbidden = temp_dirs
    sandbox = FilesystemSandbox([allowed])
    
    # Path in allowed directory
    allowed_file = allowed / "file.txt"
    assert sandbox.is_path_allowed(allowed_file) is True
    
    # Path in forbidden directory
    forbidden_file = forbidden / "file.txt"
    assert sandbox.is_path_allowed(forbidden_file) is False


def test_validate_read(temp_dirs):
    """Test validating read access."""
    allowed, _ = temp_dirs
    sandbox = FilesystemSandbox([allowed])
    
    # Create file
    file_path = allowed / "file.txt"
    file_path.write_text("test")
    
    # Should allow read
    assert sandbox.validate_read(file_path) is True


def test_validate_read_forbidden(temp_dirs):
    """Test validating read access to forbidden file."""
    allowed, forbidden = temp_dirs
    sandbox = FilesystemSandbox([allowed])
    
    # Create file in forbidden directory
    file_path = forbidden / "file.txt"
    file_path.write_text("test")
    
    # Should deny read
    assert sandbox.validate_read(file_path) is False


def test_validate_write(temp_dirs):
    """Test validating write access."""
    allowed, _ = temp_dirs
    sandbox = FilesystemSandbox([allowed])
    
    file_path = allowed / "file.txt"
    assert sandbox.validate_write(file_path) is True


def test_validate_write_forbidden(temp_dirs):
    """Test validating write access to forbidden directory."""
    allowed, forbidden = temp_dirs
    sandbox = FilesystemSandbox([allowed])
    
    file_path = forbidden / "file.txt"
    assert sandbox.validate_write(file_path) is False


def test_get_allowed_dirs(temp_dirs):
    """Test getting allowed directories."""
    allowed, _ = temp_dirs
    sandbox = FilesystemSandbox([allowed])
    
    dirs = sandbox.get_allowed_dirs()
    assert len(dirs) == 1
    assert str(allowed) in dirs
