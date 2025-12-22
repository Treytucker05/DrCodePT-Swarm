import logging
import json
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ArtifactValidator:
    def __init__(self):
        logger.info("ArtifactValidator initialized")
    
    def validate_json_artifact(self, artifact_path: Path) -> Dict[str, Any]:
        report = {"valid": True, "checks": [], "issues": [], "size_bytes": 0}
        if not artifact_path.exists():
            report["valid"] = False
            report["issues"].append("File not found")
            return report
        try:
            size = artifact_path.stat().st_size
            report["size_bytes"] = size
            if size == 0:
                report["valid"] = False
                report["issues"].append("File is empty")
                return report
            data = json.loads(artifact_path.read_text())
            report["checks"].append("✓ Valid JSON")
            if isinstance(data, dict):
                report["checks"].append(f"✓ Is dict with {len(data)} keys")
            elif isinstance(data, list):
                report["checks"].append(f"✓ Is list with {len(data)} items")
            return report
        except json.JSONDecodeError:
            report["valid"] = False
            report["issues"].append("Invalid JSON")
            return report
        except Exception:
            report["valid"] = False
            report["issues"].append("Error reading file")
            return report
    
    def validate_text_artifact(self, artifact_path: Path) -> Dict[str, Any]:
        report = {"valid": True, "checks": [], "issues": [], "size_bytes": 0, "line_count": 0}
        if not artifact_path.exists():
            report["valid"] = False
            report["issues"].append("File not found")
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
            report["checks"].append(f"✓ Valid text file ({lines} lines)")
            return report
        except Exception:
            report["valid"] = False
            report["issues"].append("Error reading file")
            return report
    
    def validate_artifacts_dir(self, artifacts_dir: Path) -> Dict[str, Any]:
        report = {"valid": True, "artifacts": {}, "total_size_bytes": 0, "issues": []}
        if not artifacts_dir.exists():
            report["valid"] = False
            report["issues"].append("Directory not found")
            return report
        for artifact_path in artifacts_dir.rglob("*"):
            if not artifact_path.is_file():
                continue
            rel_path = artifact_path.relative_to(artifacts_dir)
            if artifact_path.suffix == ".json":
                validation = self.validate_json_artifact(artifact_path)
            elif artifact_path.suffix in {".txt", ".md", ".py"}:
                validation = self.validate_text_artifact(artifact_path)
            else:
                validation = {"valid": True, "checks": ["✓ File exists"]}
            report["artifacts"][str(rel_path)] = validation
            report["total_size_bytes"] += validation.get("size_bytes", 0)
            if not validation.get("valid", True):
                report["valid"] = False
        return report
