"""
Session Memory & Context Module

This module maintains conversation context and memory across multiple tasks.
"""

import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
from collections import deque


class SessionMemory:
    """Manages session memory and context for the agent."""
    
    def __init__(self, session_id: str = None, max_history: int = 50):
        """
        Initialize session memory.
        
        Args:
            session_id: Unique session identifier (auto-generated if None)
            max_history: Maximum number of tasks to keep in memory
        """
        self.session_id = session_id or self._generate_session_id()
        self.max_history = max_history
        self.session_path = Path(f"agent/sessions/{self.session_id}")
        self.session_path.mkdir(parents=True, exist_ok=True)
        
        self.history = deque(maxlen=max_history)
        self.context = {}
        self.artifacts = {}  # Files/outputs created during session
        
        self._load_session()
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def _load_session(self):
        """Load existing session from disk."""
        session_file = self.session_path / "session.json"
        if session_file.exists():
            data = json.loads(session_file.read_text())
            self.history = deque(data.get("history", []), maxlen=self.max_history)
            self.context = data.get("context", {})
            self.artifacts = data.get("artifacts", {})
    
    def _save_session(self):
        """Save session to disk."""
        session_file = self.session_path / "session.json"
        data = {
            "session_id": self.session_id,
            "created_at": self.context.get("created_at", datetime.now().isoformat()),
            "updated_at": datetime.now().isoformat(),
            "history": list(self.history),
            "context": self.context,
            "artifacts": self.artifacts
        }
        session_file.write_text(json.dumps(data, indent=2))
    
    def add_task(self, task_def, result: Dict[str, Any]):
        """
        Add a completed task to session history.
        
        Args:
            task_def: The TaskDefinition that was executed
            result: Execution result with outcome, artifacts, etc.
        """
        task_entry = {
            "task_id": task_def.id,
            "goal": task_def.goal,
            "type": task_def.type.value,
            "timestamp": datetime.now().isoformat(),
            "outcome": result.get("outcome", "unknown"),
            "artifacts": result.get("artifacts", []),
            "duration": result.get("duration", 0)
        }
        
        self.history.append(task_entry)
        
        # Update artifacts registry
        for artifact in result.get("artifacts", []):
            self.artifacts[artifact["name"]] = {
                "path": artifact["path"],
                "created_by": task_def.id,
                "timestamp": task_entry["timestamp"]
            }
        
        self._save_session()
    
    def get_context_for_task(self, goal: str) -> Dict[str, Any]:
        """
        Get relevant context for a new task based on session history.
        
        Args:
            goal: The goal of the new task
            
        Returns:
            Dictionary with relevant context
        """
        context = {
            "session_id": self.session_id,
            "previous_tasks": list(self.history)[-5:],  # Last 5 tasks
            "available_artifacts": self.artifacts,
            "session_context": self.context
        }
        
        # Find related previous tasks
        related_tasks = []
        goal_lower = goal.lower()
        for task in self.history:
            if any(word in task["goal"].lower() for word in goal_lower.split()):
                related_tasks.append(task)
        
        if related_tasks:
            context["related_tasks"] = related_tasks[-3:]  # Last 3 related
        
        return context
    
    def set_context(self, key: str, value: Any):
        """Set a context variable."""
        self.context[key] = value
        self._save_session()
    
    def get_context(self, key: str, default=None) -> Any:
        """Get a context variable."""
        return self.context.get(key, default)
    
    def find_artifact(self, name: str) -> Optional[Dict[str, Any]]:
        """Find an artifact by name."""
        return self.artifacts.get(name)
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get a summary of the current session."""
        return {
            "session_id": self.session_id,
            "total_tasks": len(self.history),
            "successful_tasks": sum(1 for t in self.history if t["outcome"] == "success"),
            "failed_tasks": sum(1 for t in self.history if t["outcome"] != "success"),
            "artifacts_created": len(self.artifacts),
            "session_duration": self._calculate_session_duration()
        }
    
    def _calculate_session_duration(self) -> float:
        """Calculate total session duration in seconds."""
        if not self.history:
            return 0.0
        
        first_task = self.history[0]
        last_task = self.history[-1]
        
        first_time = datetime.fromisoformat(first_task["timestamp"])
        last_time = datetime.fromisoformat(last_task["timestamp"])
        
        return (last_time - first_time).total_seconds()
    
    def generate_session_report(self) -> str:
        """Generate a human-readable session report."""
        summary = self.get_session_summary()
        
        report = f"""
=================================================================
Session Report: {self.session_id}
=================================================================

Summary:
  - Total Tasks: {summary['total_tasks']}
  - Successful: {summary['successful_tasks']}
  - Failed: {summary['failed_tasks']}
  - Artifacts Created: {summary['artifacts_created']}
  - Session Duration: {summary['session_duration']:.1f}s

Recent Tasks:
"""
        
        for task in list(self.history)[-5:]:
            report += f"\n  [{task['outcome'].upper()}] {task['goal']}"
            if task['artifacts']:
                report += f"\n    → Created: {', '.join(a['name'] for a in task['artifacts'])}"
        
        if self.artifacts:
            report += "\n\nAvailable Artifacts:"
            for name, info in self.artifacts.items():
                report += f"\n  - {name}: {info['path']}"
        
        report += "\n\n=================================================================\n"
        
        return report


# Global session instance
_current_session: Optional[SessionMemory] = None


def get_current_session() -> SessionMemory:
    """Get or create the current session."""
    global _current_session
    if _current_session is None:
        _current_session = SessionMemory()
    return _current_session


def start_new_session(session_id: str = None) -> SessionMemory:
    """Start a new session."""
    global _current_session
    _current_session = SessionMemory(session_id)
    return _current_session


def end_session() -> str:
    """End the current session and return a report."""
    global _current_session
    if _current_session:
        report = _current_session.generate_session_report()
        _current_session = None
        return report
    return "No active session."


if __name__ == "__main__":
    # Test the module
    session = SessionMemory()
    
    # Simulate adding tasks
    from agent.schemas.task_schema import TaskDefinition, TaskType, StopRules, OnFailAction
    
    test_task = TaskDefinition(
        id="test-123",
        name="Test Task",
        type=TaskType.shell,
        goal="Create a test file",
        command="echo 'test'",
        definition_of_done="File created",
        stop_rules=StopRules(max_attempts=3, max_minutes=5, max_tool_calls=10),
        on_fail=OnFailAction.escalate
    )
    
    session.add_task(test_task, {
        "outcome": "success",
        "artifacts": [{"name": "test.txt", "path": "/tmp/test.txt"}],
        "duration": 2.5
    })
    
    print(session.generate_session_report())
