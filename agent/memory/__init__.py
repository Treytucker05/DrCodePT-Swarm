"""
Memory System - Persistent memory with semantic retrieval.

This module provides:
- Unified memory storage (experiences, lessons, procedures, user info)
- Semantic search via embeddings
- Reflection system for learning from task executions
"""

from .unified_memory import (
    UnifiedMemory,
    Memory,
    get_memory,
    store_experience,
    store_lesson,
    retrieve_for_planning,
)

from .reflector import (
    Reflector,
    Reflection,
    TaskExecution,
    reflect_on_task,
    get_relevant_lessons,
)

__all__ = [
    # Memory
    "UnifiedMemory",
    "Memory",
    "get_memory",
    "store_experience",
    "store_lesson",
    "retrieve_for_planning",
    # Reflection
    "Reflector",
    "Reflection",
    "TaskExecution",
    "reflect_on_task",
    "get_relevant_lessons",
]
