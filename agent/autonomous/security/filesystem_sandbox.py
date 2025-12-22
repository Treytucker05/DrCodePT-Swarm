import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

class FilesystemSandbox:
    def __init__(self, allowed_dirs: List[Path]):
        self.allowed_dirs = [d.resolve() for d in allowed_dirs]
    
    def is_path_allowed(self, path: Path) -> bool:
        path = path.resolve()
        for allowed_dir in self.allowed_dirs:
            try:
                path.relative_to(allowed_dir)
                return True
            except ValueError:
                continue
        return False
    
    def validate_read(self, path: Path) -> bool:
        if not self.is_path_allowed(path):
            return False
        return path.exists()
    
    def validate_write(self, path: Path) -> bool:
        return self.is_path_allowed(path)
    
    def validate_delete(self, path: Path) -> bool:
        return self.is_path_allowed(path)
    
    def get_allowed_dirs(self) -> List[str]:
        return [str(d) for d in self.allowed_dirs]
