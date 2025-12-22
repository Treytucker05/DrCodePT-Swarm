"""Filesystem sandbox for restricting file access."""

import logging
import os
from pathlib import Path
from typing import Set, Optional, List

logger = logging.getLogger(__name__)


class FilesystemSandbox:
    """Restrict file access to allowed directories.
    
    Prevents tasks from accessing sensitive files outside their workspace.
    """
    
    def __init__(self, allowed_dirs: List[Path]):
        """Initialize filesystem sandbox.
        
        Args:
            allowed_dirs: List of allowed directories
        """
        self.allowed_dirs = [d.resolve() for d in allowed_dirs]
        logger.info(f"FilesystemSandbox initialized with {len(self.allowed_dirs)} allowed dirs")
    
    def is_path_allowed(self, path: Path) -> bool:
        """Check if path is allowed.
        
        Args:
            path: Path to check
        
        Returns:
            True if path is within allowed directories
        """
        path = path.resolve()
        
        for allowed_dir in self.allowed_dirs:
            try:
                path.relative_to(allowed_dir)
                return True
            except ValueError:
                continue
        
        return False
    
    def validate_read(self, path: Path) -> bool:
        """Validate read access to file.
        
        Args:
            path: Path to read
        
        Returns:
            True if read is allowed
        """
        if not self.is_path_allowed(path):
            logger.warning(f"Read access denied: {path}")
            return False
        
        if not path.exists():
            logger.warning(f"File not found: {path}")
            return False
        
        return True
    
    def validate_write(self, path: Path) -> bool:
        """Validate write access to file.
        
        Args:
            path: Path to write
        
        Returns:
            True if write is allowed
        """
        if not self.is_path_allowed(path):
            logger.warning(f"Write access denied: {path}")
            return False
        
        return True
    
    def validate_delete(self, path: Path) -> bool:
        """Validate delete access to file.
        
        Args:
            path: Path to delete
        
        Returns:
            True if delete is allowed
        """
        if not self.is_path_allowed(path):
            logger.warning(f"Delete access denied: {path}")
            return False
        
        return True
    
    def get_allowed_dirs(self) -> List[str]:
        """Get list of allowed directories.
        
        Returns:
            List of allowed directory paths
        """
        return [str(d) for d in self.allowed_dirs]
