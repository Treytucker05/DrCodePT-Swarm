from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Literal, Optional


MemoryKind = Literal["experience", "procedure", "knowledge", "user_info"]


@dataclass(frozen=True)
class MemoryRecord:
    kind: MemoryKind
    id: int
    created_at: float
    updated_at: float
    key: Optional[str]
    content: str
    metadata: Dict[str, Any]


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


class SqliteMemoryStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path))
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def close(self) -> None:
        try:
            self._conn.close()
        except Exception:
            pass

    def _init_schema(self) -> None:
        cur = self._conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_records (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              kind TEXT NOT NULL,
              key TEXT,
              content TEXT NOT NULL,
              content_hash TEXT NOT NULL,
              metadata_json TEXT NOT NULL,
              created_at REAL NOT NULL,
              updated_at REAL NOT NULL,
              UNIQUE(kind, content_hash)
            );
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_memory_kind_updated ON memory_records(kind, updated_at DESC);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_memory_key ON memory_records(key);")
        self._conn.commit()

    def upsert(
        self,
        *,
        kind: MemoryKind,
        content: str,
        key: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        now = time.time()
        meta_json = json.dumps(metadata or {}, ensure_ascii=False)
        content_hash = _sha256(content.strip())
        cur = self._conn.cursor()
        cur.execute(
            """
            INSERT INTO memory_records(kind, key, content, content_hash, metadata_json, created_at, updated_at)
            VALUES(?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(kind, content_hash) DO UPDATE SET
              key=excluded.key,
              metadata_json=excluded.metadata_json,
              updated_at=excluded.updated_at;
            """,
            (kind, key, content, content_hash, meta_json, now, now),
        )
        self._conn.commit()
        return int(cur.lastrowid or 0)

    def search(
        self,
        query: str,
        *,
        kinds: Optional[List[MemoryKind]] = None,
        limit: int = 8,
    ) -> List[MemoryRecord]:
        q = (query or "").strip()
        if not q:
            return []
        like = f"%{q}%"
        kinds = kinds or ["experience", "procedure", "knowledge"]
        placeholders = ",".join("?" for _ in kinds)
        params: List[Any] = [*kinds, like, like, like, limit]
        cur = self._conn.cursor()
        cur.execute(
            f"""
            SELECT id, kind, key, content, metadata_json, created_at, updated_at
            FROM memory_records
            WHERE kind IN ({placeholders})
              AND (content LIKE ? OR key LIKE ? OR metadata_json LIKE ?)
            ORDER BY updated_at DESC
            LIMIT ?;
            """,
            params,
        )
        rows = cur.fetchall()
        out: List[MemoryRecord] = []
        for r in rows:
            out.append(
                MemoryRecord(
                    kind=r["kind"],
                    id=int(r["id"]),
                    key=r["key"],
                    content=r["content"],
                    metadata=json.loads(r["metadata_json"] or "{}"),
                    created_at=float(r["created_at"]),
                    updated_at=float(r["updated_at"]),
                )
            )
        return out

