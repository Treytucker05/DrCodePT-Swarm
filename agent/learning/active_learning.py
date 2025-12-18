"""
Active Learning & Playbook Generation Module

This module learns from successful task executions and generates reusable playbooks.
"""

import json
import hashlib
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime


class PlaybookStore:
    """Stores and retrieves learned playbooks."""
    
    def __init__(self, store_path: str = "agent/learning/playbooks"):
        self.store_path = Path(store_path)
        self.store_path.mkdir(parents=True, exist_ok=True)
        self.index_file = self.store_path / "index.json"
        self._load_index()
    
    def _load_index(self):
        """Load the playbook index."""
        if self.index_file.exists():
            self.index = json.loads(self.index_file.read_text())
        else:
            self.index = {"playbooks": [], "tags": {}}
    
    def _save_index(self):
        """Save the playbook index."""
        self.index_file.write_text(json.dumps(self.index, indent=2))
    
    def generate_playbook_from_success(
        self,
        task_def,
        execution_log: Dict[str, Any],
        run_path: Path
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a playbook from a successful task execution.
        
        Args:
            task_def: The TaskDefinition that succeeded
            execution_log: Log of the successful execution
            run_path: Path to the run directory
            
        Returns:
            Playbook dictionary
        """
        # Extract key patterns
        playbook = {
            "id": self._generate_playbook_id(task_def.goal),
            "name": f"Playbook: {task_def.name}",
            "goal_pattern": task_def.goal,
            "task_type": task_def.type.value,
            "created_at": datetime.now().isoformat(),
            "success_count": 1,
            "yaml_template": self._extract_yaml_template(task_def),
            "key_steps": self._extract_key_steps(execution_log),
            "common_pitfalls": [],
            "tags": self._extract_tags(task_def),
            "metadata": {
                "original_run": str(run_path),
                "execution_time": execution_log.get("total_time", 0),
                "tool_calls": execution_log.get("tool_calls", 0)
            }
        }
        
        return playbook
    
    def _generate_playbook_id(self, goal: str) -> str:
        """Generate a unique ID for a playbook based on the goal."""
        return hashlib.md5(goal.encode()).hexdigest()[:12]
    
    def _extract_yaml_template(self, task_def) -> str:
        """Extract a reusable YAML template from the task."""
        # Simplified - in production, would use actual YAML serialization
        return f"""id: "{{task_id}}"
name: "{task_def.name}"
type: "{task_def.type.value}"
goal: "{{goal}}"
definition_of_done: "{task_def.definition_of_done}"
stop_rules:
  max_attempts: {task_def.stop_rules.max_attempts}
  max_minutes: {task_def.stop_rules.max_minutes}
  max_tool_calls: {task_def.stop_rules.max_tool_calls}
on_fail: "{task_def.on_fail.value}"
"""
    
    def _extract_key_steps(self, execution_log: Dict[str, Any]) -> List[str]:
        """Extract key steps from the execution log."""
        steps = []
        for event in execution_log.get("events", []):
            if event.get("type") == "tool_success":
                steps.append(f"{event.get('tool')}: {event.get('action')}")
        return steps
    
    def _extract_tags(self, task_def) -> List[str]:
        """Extract relevant tags from the task."""
        tags = [task_def.type.value]
        
        # Add tags based on goal keywords
        goal_lower = task_def.goal.lower()
        if "file" in goal_lower or "create" in goal_lower:
            tags.append("file_operations")
        if "python" in goal_lower or "script" in goal_lower:
            tags.append("scripting")
        if "web" in goal_lower or "browser" in goal_lower:
            tags.append("web_automation")
        if "api" in goal_lower:
            tags.append("api_integration")
            
        return tags
    
    def save_playbook(self, playbook: Dict[str, Any]):
        """Save a playbook to the store."""
        playbook_file = self.store_path / f"{playbook['id']}.json"
        playbook_file.write_text(json.dumps(playbook, indent=2))
        
        # Update index
        existing = next((p for p in self.index["playbooks"] if p["id"] == playbook["id"]), None)
        if existing:
            existing["success_count"] += 1
            existing["updated_at"] = datetime.now().isoformat()
        else:
            self.index["playbooks"].append({
                "id": playbook["id"],
                "name": playbook["name"],
                "tags": playbook["tags"],
                "success_count": playbook["success_count"],
                "created_at": playbook["created_at"]
            })
        
        # Update tag index
        for tag in playbook["tags"]:
            if tag not in self.index["tags"]:
                self.index["tags"][tag] = []
            if playbook["id"] not in self.index["tags"][tag]:
                self.index["tags"][tag].append(playbook["id"])
        
        self._save_index()
    
    def find_playbook(self, goal: str, tags: List[str] = None) -> Optional[Dict[str, Any]]:
        """Find a matching playbook for a goal."""
        # Simple matching - in production would use embeddings/similarity
        playbook_id = self._generate_playbook_id(goal)
        playbook_file = self.store_path / f"{playbook_id}.json"
        
        if playbook_file.exists():
            return json.loads(playbook_file.read_text())
        
        # Search by tags
        if tags:
            for tag in tags:
                if tag in self.index["tags"]:
                    for pb_id in self.index["tags"][tag]:
                        pb_file = self.store_path / f"{pb_id}.json"
                        if pb_file.exists():
                            return json.loads(pb_file.read_text())
        
        return None
    
    def get_all_playbooks(self) -> List[Dict[str, Any]]:
        """Get all playbooks."""
        playbooks = []
        for pb_info in self.index["playbooks"]:
            pb_file = self.store_path / f"{pb_info['id']}.json"
            if pb_file.exists():
                playbooks.append(json.loads(pb_file.read_text()))
        return playbooks


def learn_from_success(task_def, execution_log: Dict[str, Any], run_path: Path):
    """Learn from a successful task execution."""
    store = PlaybookStore()
    
    # Generate playbook
    playbook = store.generate_playbook_from_success(task_def, execution_log, run_path)
    
    if playbook:
        store.save_playbook(playbook)
        print(f"[LEARNING] Generated playbook: {playbook['name']}")
        return playbook
    
    return None


def suggest_playbook(goal: str) -> Optional[Dict[str, Any]]:
    """Suggest a playbook for a given goal."""
    store = PlaybookStore()
    return store.find_playbook(goal)


if __name__ == "__main__":
    # Test the module
    from agent.schemas.task_schema import TaskDefinition, TaskType, StopRules, OnFailAction
    
    test_task = TaskDefinition(
        id="test-123",
        name="Test Task",
        type=TaskType.shell,
        goal="Create a Python script",
        command="echo 'test'",
        definition_of_done="Script created",
        stop_rules=StopRules(max_attempts=3, max_minutes=5, max_tool_calls=10),
        on_fail=OnFailAction.escalate
    )
    
    test_log = {
        "events": [
            {"type": "tool_success", "tool": "shell", "action": "create_file"}
        ],
        "total_time": 2.5,
        "tool_calls": 1
    }
    
    playbook = learn_from_success(test_task, test_log, Path("/tmp/test_run"))
    if playbook:
        print("Generated playbook:")
        print(json.dumps(playbook, indent=2))
