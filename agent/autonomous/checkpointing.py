import logging
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class CheckpointManager:
    def __init__(self, run_dir: Path):
        self.run_dir = run_dir
        self.checkpoint_dir = run_dir / "checkpoints"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    def save_checkpoint(self, step_num: int, state: Dict[str, Any]) -> Path:
        checkpoint_path = self.checkpoint_dir / f"checkpoint_{step_num:04d}.json"
        checkpoint_data = {"step": step_num, "timestamp": datetime.now(timezone.utc).isoformat(), "state": state}
        checkpoint_path.write_text(json.dumps(checkpoint_data, indent=2))
        return checkpoint_path
    
    def load_checkpoint(self, step_num: int) -> Optional[Dict[str, Any]]:
        checkpoint_path = self.checkpoint_dir / f"checkpoint_{step_num:04d}.json"
        if not checkpoint_path.exists():
            return None
        try:
            data = json.loads(checkpoint_path.read_text())
            return data.get("state")
        except:
            return None
    
    def list_checkpoints(self) -> List[int]:
        checkpoints = []
        for path in self.checkpoint_dir.glob("checkpoint_*.json"):
            try:
                step = int(path.stem.split("_")[1])
                checkpoints.append(step)
            except:
                pass
        return sorted(checkpoints)

    def get_latest_checkpoint(self) -> Optional[int]:
        """Get the step number of the latest checkpoint, or None if no checkpoints exist."""
        checkpoints = self.list_checkpoints()
        if not checkpoints:
            return None
        return max(checkpoints)

    def delete_checkpoint(self, step_num: int) -> bool:
        """Delete a specific checkpoint by step number. Returns True if deleted, False if not found."""
        checkpoint_path = self.checkpoint_dir / f"checkpoint_{step_num:04d}.json"
        if checkpoint_path.exists():
            checkpoint_path.unlink()
            return True
        return False

    def cleanup_old_checkpoints(self, keep_last_n: int) -> int:
        """Delete old checkpoints, keeping only the last N. Returns count of deleted checkpoints."""
        checkpoints = self.list_checkpoints()
        if len(checkpoints) <= keep_last_n:
            return 0

        to_keep = set(checkpoints[-keep_last_n:])
        deleted = 0
        for step in checkpoints:
            if step not in to_keep:
                if self.delete_checkpoint(step):
                    deleted += 1
        return deleted
