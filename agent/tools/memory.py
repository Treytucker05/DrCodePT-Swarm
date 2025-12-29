"""
Memory Tools - Stable wrappers for memory operations.

These tools wrap memory operations into stable, well-documented tool interfaces:
- memory_store: Store information in long-term memory
- memory_search: Search for similar memories
- memory_retrieve: Retrieve specific memory by key

The agent can use these directly without knowing memory internals.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Models for Tool Arguments
# ============================================================================

class MemoryStoreArgs(BaseModel):
    """Arguments for storing a memory."""
    content: str = Field(..., description="The content to store")
    kind: str = Field(
        default="knowledge",
        description="Type of memory: knowledge, procedure, experience, user_info"
    )
    key: Optional[str] = Field(
        None,
        description="Optional key for later retrieval. Auto-generated if not provided."
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional metadata to attach to the memory"
    )


class MemorySearchArgs(BaseModel):
    """Arguments for searching memories."""
    query: str = Field(..., description="Search query (semantic similarity)")
    kind: Optional[str] = Field(
        None,
        description="Filter by memory kind (knowledge, procedure, experience, user_info)"
    )
    limit: int = Field(
        default=5,
        description="Maximum number of results to return"
    )


class MemoryRetrieveArgs(BaseModel):
    """Arguments for retrieving a specific memory."""
    key: str = Field(..., description="The key of the memory to retrieve")
    kind: Optional[str] = Field(
        None,
        description="Memory kind to narrow search"
    )


class MemoryDeleteArgs(BaseModel):
    """Arguments for deleting a memory."""
    key: str = Field(..., description="The key of the memory to delete")
    kind: Optional[str] = Field(
        None,
        description="Memory kind to narrow search"
    )


# ============================================================================
# Tool Implementations
# ============================================================================

def _get_memory_store():
    """Get the memory store instance."""
    try:
        from agent.autonomous.memory.sqlite_store import SqliteMemoryStore
        from pathlib import Path

        agent_root = Path(__file__).resolve().parents[1]
        db_path = agent_root / "memory" / "autonomous_memory.sqlite3"
        return SqliteMemoryStore(db_path)
    except Exception as e:
        logger.error(f"Failed to get memory store: {e}")
        return None


def memory_store(ctx, args: MemoryStoreArgs):
    """
    Store information in long-term memory.

    Returns the record ID of the stored memory.
    """
    from agent.autonomous.models import ToolResult

    try:
        store = _get_memory_store()
        if store is None:
            return ToolResult(
                success=False,
                error="Memory store not available",
                retryable=True,
            )

        # Validate kind
        valid_kinds = {"knowledge", "procedure", "experience", "user_info"}
        kind = args.kind if args.kind in valid_kinds else "knowledge"

        # Store the memory
        record_id = store.upsert(
            kind=kind,
            key=args.key,
            content=args.content[:8000],  # Limit content size
            metadata=args.metadata or {},
        )

        store.close()

        return ToolResult(
            success=True,
            output={
                "message": f"Stored memory with ID {record_id}",
                "record_id": record_id,
                "kind": kind,
                "key": args.key,
            },
        )

    except Exception as e:
        logger.error(f"memory_store failed: {e}")
        return ToolResult(
            success=False,
            error=str(e),
            retryable=True,
        )


def memory_search(ctx, args: MemorySearchArgs):
    """
    Search for similar memories.

    Returns list of matching memories with content and metadata.
    """
    from agent.autonomous.models import ToolResult

    try:
        store = _get_memory_store()
        if store is None:
            return ToolResult(
                success=False,
                error="Memory store not available",
                retryable=True,
            )

        # Search memories
        results = store.search(args.query, limit=args.limit)

        # Filter by kind if specified
        if args.kind:
            results = [r for r in results if r.kind == args.kind]

        # Format results
        memories = []
        for r in results:
            memories.append({
                "id": r.id,
                "kind": r.kind,
                "key": r.key,
                "content": r.content[:2000],  # Truncate for response
                "metadata": r.metadata,
                "updated_at": r.updated_at,
            })

        store.close()

        return ToolResult(
            success=True,
            output={
                "query": args.query,
                "count": len(memories),
                "memories": memories,
            },
        )

    except Exception as e:
        logger.error(f"memory_search failed: {e}")
        return ToolResult(
            success=False,
            error=str(e),
            retryable=True,
        )


def memory_retrieve(ctx, args: MemoryRetrieveArgs):
    """
    Retrieve a specific memory by key.

    Returns the memory content and metadata.
    """
    from agent.autonomous.models import ToolResult

    try:
        store = _get_memory_store()
        if store is None:
            return ToolResult(
                success=False,
                error="Memory store not available",
                retryable=True,
            )

        # Search by key
        results = store.search(args.key, limit=10)

        # Find exact key match
        memory = None
        for r in results:
            if r.key == args.key:
                if args.kind is None or r.kind == args.kind:
                    memory = r
                    break

        store.close()

        if memory is None:
            return ToolResult(
                success=False,
                error=f"Memory with key '{args.key}' not found",
                retryable=False,
            )

        return ToolResult(
            success=True,
            output={
                "id": memory.id,
                "kind": memory.kind,
                "key": memory.key,
                "content": memory.content,
                "metadata": memory.metadata,
                "updated_at": memory.updated_at,
            },
        )

    except Exception as e:
        logger.error(f"memory_retrieve failed: {e}")
        return ToolResult(
            success=False,
            error=str(e),
            retryable=True,
        )


def memory_delete(ctx, args: MemoryDeleteArgs):
    """
    Delete a memory by key.

    Note: This is a soft delete in most implementations.
    """
    from agent.autonomous.models import ToolResult

    try:
        store = _get_memory_store()
        if store is None:
            return ToolResult(
                success=False,
                error="Memory store not available",
                retryable=True,
            )

        # Search by key to find the memory
        results = store.search(args.key, limit=10)

        # Find exact key match
        memory = None
        for r in results:
            if r.key == args.key:
                if args.kind is None or r.kind == args.kind:
                    memory = r
                    break

        if memory is None:
            store.close()
            return ToolResult(
                success=False,
                error=f"Memory with key '{args.key}' not found",
                retryable=False,
            )

        # Delete by upserting empty content (soft delete)
        # Most SQLite memory stores don't have a hard delete
        store.upsert(
            kind=memory.kind,
            key=memory.key,
            content="[DELETED]",
            metadata={"deleted": True, "original_id": memory.id},
        )

        store.close()

        return ToolResult(
            success=True,
            output={
                "message": f"Deleted memory with key '{args.key}'",
                "id": memory.id,
            },
        )

    except Exception as e:
        logger.error(f"memory_delete failed: {e}")
        return ToolResult(
            success=False,
            error=str(e),
            retryable=True,
        )


# ============================================================================
# Tool Specs for Registry
# ============================================================================

MEMORY_TOOL_SPECS = [
    {
        "name": "memory_store",
        "args_model": MemoryStoreArgs,
        "fn": memory_store,
        "description": "Store information in long-term memory for later retrieval",
    },
    {
        "name": "memory_search",
        "args_model": MemorySearchArgs,
        "fn": memory_search,
        "description": "Search for similar memories using semantic search",
    },
    {
        "name": "memory_retrieve",
        "args_model": MemoryRetrieveArgs,
        "fn": memory_retrieve,
        "description": "Retrieve a specific memory by its key",
    },
    {
        "name": "memory_delete",
        "args_model": MemoryDeleteArgs,
        "fn": memory_delete,
        "description": "Delete a memory by its key",
    },
]


def register_memory_tools(registry) -> None:
    """Register all memory tools with a ToolRegistry."""
    from agent.autonomous.tools.registry import ToolSpec

    for spec in MEMORY_TOOL_SPECS:
        registry.register(ToolSpec(
            name=spec["name"],
            args_model=spec["args_model"],
            fn=spec["fn"],
            description=spec["description"],
        ))


__all__ = [
    "MemoryStoreArgs",
    "MemorySearchArgs",
    "MemoryRetrieveArgs",
    "MemoryDeleteArgs",
    "memory_store",
    "memory_search",
    "memory_retrieve",
    "memory_delete",
    "register_memory_tools",
    "MEMORY_TOOL_SPECS",
]
