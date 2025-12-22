"""QA subagent for validating task results."""

import logging
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class QAAgent:
    """Quality assurance agent for validating results.
    
    Checks:
    - Artifact completeness
    - Code validity
    - Research quality
    - Result consistency
    """
    
    def __init__(self):
        """Initialize QA agent."""
        self.checks_passed = 0
        self.checks_failed = 0
        logger.info("QAAgent initialized")
    
    def validate_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a task result.
        
        Args:
            result: Result dict from task execution
        
        Returns:
            Validation report
        """
        report = {
            "valid": True,
            "checks": [],
            "issues": [],
            "score": 0.0,
        }
        
        # Check 1: Result has required fields
        required_fields = ["status", "task_id"]
        for field in required_fields:
            if field in result:
                report["checks"].append(f"? Has field: {field}")
                self.checks_passed += 1
            else:
                report["checks"].append(f"? Missing field: {field}")
                report["issues"].append(f"Missing required field: {field}")
                report["valid"] = False
                self.checks_failed += 1
        
        # Check 2: Status is valid
        valid_statuses = ["success", "partial_failure", "failure"]
        if result.get("status") in valid_statuses:
            report["checks"].append(f"? Valid status: {result['status']}")
            self.checks_passed += 1
        else:
            report["checks"].append(f"? Invalid status: {result.get('status')}")
            report["issues"].append(f"Invalid status: {result.get('status')}")
            report["valid"] = False
            self.checks_failed += 1
        
        # Check 3: Has artifacts or output
        has_output = bool(result.get("artifacts") or result.get("output") or result.get("data"))
        if has_output:
            report["checks"].append("? Has output/artifacts")
            self.checks_passed += 1
        else:
            report["checks"].append("? No output/artifacts")
            report["issues"].append("Result has no output or artifacts")
            report["valid"] = False
            self.checks_failed += 1
        
        # Check 4: No fatal errors
        has_errors = bool(result.get("errors"))
        if not has_errors:
            report["checks"].append("? No fatal errors")
            self.checks_passed += 1
        else:
            report["checks"].append(f"? Has errors: {result['errors']}")
            report["issues"].append(f"Result has errors: {result['errors']}")
            self.checks_failed += 1
        
        # Calculate score
        total_checks = self.checks_passed + self.checks_failed
        if total_checks > 0:
            report["score"] = (self.checks_passed / total_checks) * 100
        
        logger.info(
            f"QA validation complete: {report['score']:.1f}% "
            f"({len(report['issues'])} issues)"
        )
        return report
    
    def validate_code(self, code: str) -> Dict[str, Any]:
        """Validate Python code.
        
        Args:
            code: Python code to validate
        
        Returns:
            Validation report
        """
        report = {
            "valid": True,
            "checks": [],
            "issues": [],
        }
        
        # Check 1: Can compile
        try:
            compile(code, "<string>", "exec")
            report["checks"].append("? Code compiles")
        except SyntaxError as exc:
            report["checks"].append(f"? Syntax error: {exc}")
            report["issues"].append(f"Syntax error: {exc}")
            report["valid"] = False
        
        # Check 2: No obvious security issues
        dangerous_patterns = ["eval(", "exec(", "__import__", "os.system"]
        found_dangerous = []
        for pattern in dangerous_patterns:
            if pattern in code:
                found_dangerous.append(pattern)
        
        if not found_dangerous:
            report["checks"].append("? No dangerous patterns")
        else:
            report["checks"].append(f"? Found dangerous patterns: {found_dangerous}")
            report["issues"].append(f"Dangerous patterns: {found_dangerous}")
            report["valid"] = False
        
        # Check 3: Has docstrings for functions
        import ast
        try:
            tree = ast.parse(code)
            functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            documented = sum(1 for f in functions if ast.get_docstring(f))
            
            if functions:
                doc_ratio = documented / len(functions)
                if doc_ratio >= 0.5:
                    report["checks"].append(f"? {doc_ratio*100:.0f}% functions documented")
                else:
                    report["checks"].append(f"? Only {doc_ratio*100:.0f}% functions documented")
                    report["issues"].append("Low documentation coverage")
        except Exception as exc:
            logger.warning(f"Could not analyze code structure: {exc}")
        
        return report
    
    def validate_research(self, research: Dict[str, Any]) -> Dict[str, Any]:
        """Validate research quality.
        
        Args:
            research: Research data with sources
        
        Returns:
            Validation report
        """
        report = {
            "valid": True,
            "checks": [],
            "issues": [],
        }
        
        # Check 1: Has sources
        sources = research.get("sources", [])
        if sources:
            report["checks"].append(f"? Has {len(sources)} sources")
        else:
            report["checks"].append("? No sources cited")
            report["issues"].append("Research has no sources")
            report["valid"] = False
        
        # Check 2: Sources are diverse
        if sources and len(set(s.get("domain", "") for s in sources)) > 1:
            report["checks"].append("? Sources are diverse")
        elif sources:
            report["checks"].append("? Sources are not diverse")
            report["issues"].append("All sources from same domain")
        
        # Check 3: Has summary
        if research.get("summary"):
            report["checks"].append("? Has summary")
        else:
            report["checks"].append("? No summary")
            report["issues"].append("Research has no summary")
            report["valid"] = False
        
        return report
    
    def get_summary(self) -> Dict[str, Any]:
        """Get QA summary.
        
        Returns:
            Summary dict
        """
        total = self.checks_passed + self.checks_failed
        return {
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "total_checks": total,
            "pass_rate": (self.checks_passed / total * 100) if total > 0 else 0,
        }
