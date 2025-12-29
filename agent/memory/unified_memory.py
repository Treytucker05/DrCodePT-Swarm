"""
Unified Memory System - Ensures consistent memory persistence and retrieval.

This module wraps the existing memory stores and ensures:
- Reflections are stored as knowledge
- Past experiences are retrieved during planning
- Memory persists across sessions
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

logger = logging.getLogger(__name__)

MemoryKind = Literal["experience", "procedure", "knowledge", "user_info"]

# Default database path
DEFAULT_DB_PATH = Path.home() / ".drcodept" / "memory.db"


@dataclass
class Memory:
    """A memory entry."""
    id: int
    kind: MemoryKind
    content: str
    key: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = 0.0
    updated_at: float = 0.0
    relevance_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "content": self.content,
            "key": self.key,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "relevance_score": self.relevance_score,
        }


class UnifiedMemory:
    """
    Unified memory system that wraps SQLite store.

    Provides high-level operations for:
    - Storing task experiences
    - Storing reflection lessons
    - Retrieving relevant memories for planning
    - Persisting user preferences
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize unified memory.

        Args:
            db_path: Path to SQLite database. If None, uses default.
        """
        self._db_path = db_path or Path(os.getenv(
            "AGENT_MEMORY_DB",
            str(DEFAULT_DB_PATH)
        ))
        self._store = None

    def _get_store(self):
        """Lazy-load the SQLite store."""
        if self._store is None:
            try:
                from agent.autonomous.memory.sqlite_store import SqliteMemoryStore
                self._store = SqliteMemoryStore(self._db_path)
            except Exception as e:
                logger.error(f"Failed to initialize memory store: {e}")
                raise
        return self._store

    def store_experience(
        self,
        task: str,
        result: str,
        success: bool,
        duration_seconds: float = 0.0,
        tools_used: Optional[List[str]] = None,
    ) -> int:
        """
        Store a task execution experience.

        Args:
            task: The task that was executed
            result: The outcome/result of the task
            success: Whether the task succeeded
            duration_seconds: How long the task took
            tools_used: List of tools that were used

        Returns:
            Memory record ID
        """
        content = f"Task: {task}\nResult: {result}"
        metadata = {
            "success": success,
            "duration_seconds": duration_seconds,
            "tools_used": tools_used or [],
            "timestamp": datetime.now().isoformat(),
        }

        store = self._get_store()
        return store.upsert(
            kind="experience",
            content=content,
            metadata=metadata,
        )

    def store_lesson(
        self,
        lesson: str,
        context: str,
        tags: Optional[List[str]] = None,
    ) -> int:
        """
        Store a reflection lesson learned.

        Args:
            lesson: The lesson/insight learned
            context: Context in which the lesson was learned
            tags: Optional tags for categorization

        Returns:
            Memory record ID
        """
        content = f"Lesson: {lesson}\nContext: {context}"
        metadata = {
            "type": "lesson",
            "tags": tags or [],
            "timestamp": datetime.now().isoformat(),
        }

        store = self._get_store()
        return store.upsert(
            kind="knowledge",
            content=content,
            key=f"lesson:{hash(lesson) % 1000000}",
            metadata=metadata,
        )

    def store_procedure(
        self,
        name: str,
        steps: List[str],
        description: str = "",
    ) -> int:
        """
        Store a learned procedure.

        Args:
            name: Procedure name
            steps: List of steps to execute
            description: Optional description

        Returns:
            Memory record ID
        """
        content = f"Procedure: {name}\nDescription: {description}\nSteps:\n"
        content += "\n".join(f"  {i+1}. {step}" for i, step in enumerate(steps))

        metadata = {
            "type": "procedure",
            "step_count": len(steps),
            "timestamp": datetime.now().isoformat(),
        }

        store = self._get_store()
        return store.upsert(
            kind="procedure",
            content=content,
            key=f"procedure:{name}",
            metadata=metadata,
        )

    def store_user_info(
        self,
        key: str,
        value: str,
    ) -> int:
        """
        Store user preference or information.

        Args:
            key: The info key (e.g., "preferred_language")
            value: The value

        Returns:
            Memory record ID
        """
        content = f"{key}: {value}"
        metadata = {
            "type": "user_info",
            "timestamp": datetime.now().isoformat(),
        }

        store = self._get_store()
        return store.upsert(
            kind="user_info",
            content=content,
            key=f"user:{key}",
            metadata=metadata,
        )

    def retrieve(
        self,
        query: str,
        kinds: Optional[List[MemoryKind]] = None,
        limit: int = 5,
    ) -> List[Memory]:
        """
        Retrieve relevant memories for a query.

        Args:
            query: Search query
            kinds: Types of memories to search (default: all)
            limit: Maximum number of results

        Returns:
            List of relevant memories
        """
        store = self._get_store()
        records = store.search(
            query,
            kinds=kinds,
            limit=limit,
        )

        return [
            Memory(
                id=r.id,
                kind=r.kind,
                content=r.content,
                key=r.key,
                metadata=r.metadata,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in records
        ]

    def retrieve_for_planning(self, task: str, limit: int = 5) -> List[Memory]:
        """
        Retrieve memories relevant for planning a task.

        Searches experiences, procedures, and knowledge.

        Args:
            task: The task to plan for
            limit: Maximum memories to retrieve

        Returns:
            List of relevant memories
        """
        return self.retrieve(
            task,
            kinds=["experience", "procedure", "knowledge"],
            limit=limit,
        )

    def get_user_preferences(self) -> Dict[str, str]:
        """
        Get all stored user preferences.

        Returns:
            Dict of key-value preferences
        """
        store = self._get_store()
        records = store.search(
            "user preference",
            kinds=["user_info"],
            limit=50,
        )

        preferences = {}
        for r in records:
            if r.key and r.key.startswith("user:"):
                key = r.key[5:]  # Remove "user:" prefix
                # Extract value from content
                if ": " in r.content:
                    value = r.content.split(": ", 1)[1]
                    preferences[key] = value

        return preferences


# Global instance
_memory: Optional[UnifiedMemory] = None


def get_memory() -> UnifiedMemory:
    """Get the global memory instance."""
    global _memory
    if _memory is None:
        _memory = UnifiedMemory()
    return _memory


def store_experience(
    task: str,
    result: str,
    success: bool,
    **kwargs,
) -> int:
    """Convenience function to store an experience."""
    return get_memory().store_experience(task, result, success, **kwargs)


def store_lesson(lesson: str, context: str, **kwargs) -> int:
    """Convenience function to store a lesson."""
    return get_memory().store_lesson(lesson, context, **kwargs)


def retrieve_for_planning(task: str, limit: int = 5) -> List[Memory]:
    """Convenience function to retrieve memories for planning."""
    return get_memory().retrieve_for_planning(task, limit)
