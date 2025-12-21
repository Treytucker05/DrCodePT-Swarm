from __future__ import annotations

from agent.autonomous.memory.sqlite_store import SqliteMemoryStore


def test_memory_store_hash_embedding_search(tmp_path) -> None:
    store = SqliteMemoryStore(tmp_path / "memory.sqlite3")
    try:
        store.upsert(kind="knowledge", content="amazon order tracking info")
        store.upsert(kind="knowledge", content="github issue triage steps")

        results = store.search("amazon tracking", limit=5)
        assert results
        assert any("amazon" in r.content.lower() for r in results)

        cur = store._conn.cursor()
        cols = {row["name"] for row in cur.execute("PRAGMA table_info(memory_embeddings)")}
        assert "model" in cols
        row = cur.execute("SELECT model FROM memory_embeddings LIMIT 1").fetchone()
        assert row is not None
        model = row["model"]
        if model is not None:
            assert str(model).startswith("hash")
    finally:
        store.close()
