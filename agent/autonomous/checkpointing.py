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
