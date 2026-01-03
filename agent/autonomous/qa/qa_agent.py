import logging
from typing import Dict, Any
import ast

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
            report["issues"].append(f"Invalid status: {result.get('status')}")
            report["valid"] = False
            self.checks_failed += 1
        total_checks = self.checks_passed + self.checks_failed
        if total_checks > 0:
            report["score"] = (self.checks_passed / total_checks) * 100
        return report
    
    def validate_code(self, code: str) -> Dict[str, Any]:
        report = {"valid": True, "checks": [], "issues": []}
        # Check syntax
        try:
            ast.parse(code)
            report["checks"].append("✓ Valid syntax")
        except SyntaxError as e:
            report["checks"].append("✗ Syntax error")
            report["issues"].append(f"Syntax error: {e}")
            report["valid"] = False
        # Check for dangerous patterns
        dangerous_patterns = ["eval(", "exec(", "__import__("]
        for pattern in dangerous_patterns:
            if pattern in code:
                report["checks"].append(f"✗ Dangerous pattern: {pattern}")
                report["issues"].append(f"Dangerous pattern detected: {pattern}")
                report["valid"] = False
        return report
    
    def validate_research(self, research: Dict[str, Any]) -> Dict[str, Any]:
        report = {"valid": True, "checks": [], "issues": []}
        if "summary" in research and research["summary"]:
            report["checks"].append("✓ Has summary")
        else:
            report["checks"].append("✗ Missing or empty summary")
            report["issues"].append("Missing or empty summary")
            report["valid"] = False
        if "sources" in research and isinstance(research["sources"], list) and len(research["sources"]) > 0:
            report["checks"].append("✓ Has sources")
        else:
            report["checks"].append("✗ Missing or empty sources")
            report["issues"].append("Missing or empty sources")
            report["valid"] = False
        return report
    
    def get_summary(self) -> Dict[str, Any]:
        total = self.checks_passed + self.checks_failed
        return {"checks_passed": self.checks_passed, "checks_failed": self.checks_failed, "total_checks": total, "pass_rate": (self.checks_passed / total * 100) if total > 0 else 0}
