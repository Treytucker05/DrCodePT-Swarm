"""
Issue Tracker for Agent Self-Healing.

Tracks errors, solutions, and retry attempts during autonomous execution.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ISSUES_DIR = REPO_ROOT / "agent" / "memory" / "issues"
ISSUES_DIR.mkdir(parents=True, exist_ok=True)

class Issue:
    def __init__(
        self,
        issue_id: str,
        task: str,
        error: str,
        context: Dict[str, Any],
        timestamp: Optional[str] = None
    ):
        self.issue_id = issue_id
        self.task = task
        self.error = error
        self.context = context
        self.timestamp = timestamp or datetime.now().isoformat()
        self.attempts: List[Dict[str, Any]] = []
        self.status = "open"
        self.solution: Optional[str] = None
    
    def add_attempt(self, solution: str, result: str, success: bool):
        """Record a solution attempt."""
        self.attempts.append({
            "solution": solution,
            "result": result,
            "success": success,
            "timestamp": datetime.now().isoformat()
        })
        if success:
            self.status = "resolved"
            self.solution = solution
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_id": self.issue_id,
            "task": self.task,
            "error": self.error,
            "context": self.context,
            "timestamp": self.timestamp,
            "attempts": self.attempts,
            "status": self.status,
            "solution": self.solution
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Issue":
        issue = cls(
            issue_id=data["issue_id"],
            task=data["task"],
            error=data["error"],
            context=data["context"],
            timestamp=data.get("timestamp")
        )
        issue.attempts = data.get("attempts", [])
        issue.status = data.get("status", "open")
        issue.solution = data.get("solution")
        return issue

def save_issue(issue: Issue) -> Path:
    """Save issue to disk."""
    issue_file = ISSUES_DIR / f"{issue.issue_id}.json"
    with open(issue_file, "w") as f:
        json.dump(issue.to_dict(), f, indent=2)
    return issue_file

def load_issue(issue_id: str) -> Optional[Issue]:
    """Load issue from disk."""
    issue_file = ISSUES_DIR / f"{issue_id}.json"
    if not issue_file.exists():
        return None
    
    with open(issue_file, "r") as f:
        data = json.load(f)
    return Issue.from_dict(data)

def list_issues(status: Optional[str] = None) -> List[Issue]:
    """List all issues, optionally filtered by status."""
    issues = []
    for issue_file in ISSUES_DIR.glob("*.json"):
        with open(issue_file, "r") as f:
            data = json.load(f)
        issue = Issue.from_dict(data)
        if status is None or issue.status == status:
            issues.append(issue)
    return sorted(issues, key=lambda x: x.timestamp, reverse=True)

def find_similar_issue(task: str, error: str) -> Optional[Issue]:
    """Find a similar resolved issue for reference."""
    resolved_issues = list_issues(status="resolved")
    
    for issue in resolved_issues:
        if error.lower() in issue.error.lower() or issue.error.lower() in error.lower():
            return issue
        
        task_words = set(task.lower().split())
        issue_words = set(issue.task.lower().split())
        overlap = len(task_words & issue_words) / max(len(task_words), len(issue_words))
        if overlap > 0.5:
            return issue
    
    return None

def create_issue(task: str, error: str, context: Dict[str, Any]) -> Issue:
    """Create a new issue."""
    issue_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    issue = Issue(issue_id, task, error, context)
    save_issue(issue)
    return issue

def update_issue(issue: Issue):
    """Update an existing issue."""
    save_issue(issue)

def get_issue_summary() -> Dict[str, int]:
    """Get summary of issues by status."""
    all_issues = list_issues()
    summary = {"open": 0, "resolved": 0, "total": len(all_issues)}
    for issue in all_issues:
        if issue.status == "open":
            summary["open"] += 1
        elif issue.status == "resolved":
            summary["resolved"] += 1
    return summary

__all__ = [
    "Issue",
    "save_issue",
    "load_issue",
    "list_issues",
    "find_similar_issue",
    "create_issue",
    "update_issue",
    "get_issue_summary"
]
