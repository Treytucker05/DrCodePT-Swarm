import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class QAAgent:
    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
    
    def validate_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        report = {"valid": True, "checks": [], "issues": [], "score": 0.0}
        required_fields = ["status", "task_id"]
        for field in required_fields:
            if field in result:
                report["checks"].append(f"✓ Has field: {field}")
                self.checks_passed += 1
            else:
                report["checks"].append(f"✗ Missing field: {field}")
                report["issues"].append(f"Missing required field: {field}")
                report["valid"] = False
                self.checks_failed += 1
        valid_statuses = ["success", "partial_failure", "failure"]
        if result.get("status") in valid_statuses:
            report["checks"].append(f"✓ Valid status")
            self.checks_passed += 1
        else:
            report["checks"].append(f"✗ Invalid status")
            report["valid"] = False
            self.checks_failed += 1
        total_checks = self.checks_passed + self.checks_failed
        if total_checks > 0:
            report["score"] = (self.checks_passed / total_checks) * 100
        return report
    
    def get_summary(self) -> Dict[str, Any]:
        total = self.checks_passed + self.checks_failed
        return {"checks_passed": self.checks_passed, "checks_failed": self.checks_failed, "total_checks": total, "pass_rate": (self.checks_passed / total * 100) if total > 0 else 0}
