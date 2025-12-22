"""Artifact validation utilities."""

import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class ArtifactValidator:
    """Validate artifacts produced by tasks."""
    
    def __init__(self):
        """Initialize artifact validator."""
        logger.info("ArtifactValidator initialized")
    
    def validate_json_artifact(self, artifact_path: Path) -> Dict[str, Any]:
        """Validate JSON artifact.
        
        Args:
            artifact_path: Path to JSON file
        
        Returns:
            Validation report
        """
        report = {
            "valid": True,
            "checks": [],
            "issues": [],
            "size_bytes": 0,
        }
        
        if not artifact_path.exists():
            report["valid"] = False
            report["issues"].append(f"File not found: {artifact_path}")
            return report
        
        try:
            # Check file size
            size = artifact_path.stat().st_size
            report["size_bytes"] = size
            
            if size == 0:
                report["valid"] = False
                report["issues"].append("File is empty")
                return report
            
            if size > 100_000_000:  # 100MB
                report["issues"].append(f"File is very large: {size / 1024 / 1024:.1f}MB")
            
            # Try to parse JSON
            data = json.loads(artifact_path.read_text())
            report["checks"].append("? Valid JSON")
            
            # Check structure
            if isinstance(data, dict):
                report["checks"].append(f"? Is dict with {len(data)} keys")
            elif isinstance(data, list):
                report["checks"].append(f"? Is list with {len(data)} items")
            else:
                report["checks"].append(f"? Is {type(data).__name__}")
            
            return report
        
        except json.JSONDecodeError as exc:
            report["valid"] = False
            report["issues"].append(f"Invalid JSON: {exc}")
            return report
        except Exception as exc:
            report["valid"] = False
            report["issues"].append(f"Error reading file: {exc}")
            return report
    
    def validate_text_artifact(self, artifact_path: Path) -> Dict[str, Any]:
        """Validate text artifact.
        
        Args:
            artifact_path: Path to text file
        
        Returns:
            Validation report
        """
        report = {
            "valid": True,
            "checks": [],
            "issues": [],
            "size_bytes": 0,
            "line_count": 0,
        }
        
        if not artifact_path.exists():
            report["valid"] = False
            report["issues"].append(f"File not found: {artifact_path}")
            return report
        
        try:
            content = artifact_path.read_text()
            size = len(content.encode())
            lines = len(content.splitlines())
            
            report["size_bytes"] = size
            report["line_count"] = lines
            
            if size == 0:
                report["valid"] = False
                report["issues"].append("File is empty")
                return report
            
            report["checks"].append(f"? Valid text file ({lines} lines)")
            
            # Check for common issues
            if lines > 10000:
                report["issues"].append(f"Very large file: {lines} lines")
            
            return report
        
        except Exception as exc:
            report["valid"] = False
            report["issues"].append(f"Error reading file: {exc}")
            return report
    
    def validate_artifacts_dir(self, artifacts_dir: Path) -> Dict[str, Any]:
        """Validate all artifacts in directory.
        
        Args:
            artifacts_dir: Directory containing artifacts
        
        Returns:
            Validation report
        """
        report = {
            "valid": True,
            "artifacts": {},
            "total_size_bytes": 0,
            "issues": [],
        }
        
        if not artifacts_dir.exists():
            report["valid"] = False
            report["issues"].append(f"Directory not found: {artifacts_dir}")
            return report
        
        for artifact_path in artifacts_dir.rglob("*"):
            if not artifact_path.is_file():
                continue
            
            rel_path = artifact_path.relative_to(artifacts_dir)
            
            # Validate based on file type
            if artifact_path.suffix == ".json":
                validation = self.validate_json_artifact(artifact_path)
            elif artifact_path.suffix in {".txt", ".md", ".py"}:
                validation = self.validate_text_artifact(artifact_path)
            else:
                validation = {"valid": True, "checks": ["? File exists"]}
            
            report["artifacts"][str(rel_path)] = validation
            report["total_size_bytes"] += validation.get("size_bytes", 0)
            
            if not validation.get("valid", True):
                report["valid"] = False
        
        return report
