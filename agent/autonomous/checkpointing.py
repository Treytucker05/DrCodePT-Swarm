"""Checkpoint management for resumable runs."""

import logging
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class CheckpointManager:
    """Manage checkpoints for resumable execution."""

    def __init__(self, run_dir: Path):
        """Initialize checkpoint manager.

        Args:
            run_dir: Directory to store checkpoints
        """
        self.run_dir = run_dir
        self.checkpoint_dir = run_dir / "checkpoints"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Checkpoint manager initialized: {self.checkpoint_dir}")

    def save_checkpoint(self, step_num: int, state: Dict[str, Any]) -> Path:
        """Save checkpoint at step.

        Args:
            step_num: Step number
            state: State to save (dict)

        Returns:
            Path to checkpoint file
        """
        checkpoint_path = self.checkpoint_dir / f"checkpoint_{step_num:04d}.json"

        checkpoint_data = {
            "step": step_num,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "state": state,
        }

        checkpoint_path.write_text(json.dumps(checkpoint_data, indent=2))
        logger.info(f"Saved checkpoint: {checkpoint_path}")
        return checkpoint_path

    def load_checkpoint(self, step_num: int) -> Optional[Dict[str, Any]]:
        """Load checkpoint from step.

        Args:
            step_num: Step number

        Returns:
            State dict or None if checkpoint doesn't exist
        """
        checkpoint_path = self.checkpoint_dir / f"checkpoint_{step_num:04d}.json"

        if not checkpoint_path.exists():
            logger.warning(f"Checkpoint not found: {checkpoint_path}")
            return None

        try:
            data = json.loads(checkpoint_path.read_text())
            logger.info(f"Loaded checkpoint: {checkpoint_path}")
            return data.get("state")
        except Exception as exc:
            logger.error(f"Error loading checkpoint: {exc}", exc_info=True)
            return None

    def list_checkpoints(self) -> List[int]:
        """List available checkpoint steps.

        Returns:
            List of step numbers in order
        """
        checkpoints = []

        for path in self.checkpoint_dir.glob("checkpoint_*.json"):
            try:
                step = int(path.stem.split("_")[1])
                checkpoints.append(step)
            except (ValueError, IndexError):
                logger.warning(f"Invalid checkpoint filename: {path}")

        return sorted(checkpoints)

    def get_latest_checkpoint(self) -> Optional[int]:
        """Get the latest checkpoint step.

        Returns:
            Latest step number or None if no checkpoints
        """
        checkpoints = self.list_checkpoints()
        return checkpoints[-1] if checkpoints else None

    def delete_checkpoint(self, step_num: int) -> bool:
        """Delete a checkpoint.

        Args:
            step_num: Step number

        Returns:
            True if deleted, False if not found
        """
        checkpoint_path = self.checkpoint_dir / f"checkpoint_{step_num:04d}.json"

        if not checkpoint_path.exists():
            return False

        checkpoint_path.unlink()
        logger.info(f"Deleted checkpoint: {checkpoint_path}")
        return True

    def cleanup_old_checkpoints(self, keep_last_n: int = 5) -> int:
        """Delete old checkpoints, keeping only the last N.

        Args:
            keep_last_n: Number of recent checkpoints to keep

        Returns:
            Number of checkpoints deleted
        """
        checkpoints = self.list_checkpoints()

        if len(checkpoints) <= keep_last_n:
            return 0

        to_delete = checkpoints[:-keep_last_n]
        deleted_count = 0

        for step in to_delete:
            if self.delete_checkpoint(step):
                deleted_count += 1

        logger.info(f"Cleaned up {deleted_count} old checkpoints")
        return deleted_count
