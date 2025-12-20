from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Literal, Optional


MemoryKind = Literal["experience", "procedure", "knowledge", "user_info"]

_EMBED_DIM = 256


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", (text or "").lower())


def _embed(text: str, dim: int = _EMBED_DIM) -> tuple[List[float], float]:
    vec = [0.0] * dim
    for tok in _tokenize(text):
        h = int(hashlib.md5(tok.encode("utf-8", errors="replace")).hexdigest(), 16)
        idx = h % dim
        vec[idx] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return vec, norm


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
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_embeddings (
              record_id INTEGER PRIMARY KEY,
              dim INTEGER NOT NULL,
              vector_json TEXT NOT NULL,
              norm REAL NOT NULL,
              updated_at REAL NOT NULL,
              FOREIGN KEY(record_id) REFERENCES memory_records(id) ON DELETE CASCADE
            );
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_memory_kind_updated ON memory_records(kind, updated_at DESC);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_memory_key ON memory_records(key);")
        self._conn.commit()

    def _upsert_embedding(self, record_id: int, content: str, *, now: Optional[float] = None) -> None:
        now = now or time.time()
        vec, norm = _embed(content)
        cur = self._conn.cursor()
        cur.execute(
            """
            INSERT INTO memory_embeddings(record_id, dim, vector_json, norm, updated_at)
            VALUES(?, ?, ?, ?, ?)
            ON CONFLICT(record_id) DO UPDATE SET
              vector_json=excluded.vector_json,
              norm=excluded.norm,
              updated_at=excluded.updated_at;
            """,
            (record_id, _EMBED_DIM, json.dumps(vec), float(norm), now),
        )
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
        rec_id = int(cur.lastrowid or 0)
        if rec_id == 0:
            try:
                row = cur.execute(
                    "SELECT id FROM memory_records WHERE kind=? AND content_hash=? LIMIT 1",
                    (kind, content_hash),
                ).fetchone()
                if row is not None:
                    rec_id = int(row["id"])
            except Exception:
                rec_id = 0
        if rec_id:
            try:
                self._upsert_embedding(rec_id, content, now=now)
            except Exception:
                pass
        return rec_id

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
        kinds = kinds or ["experience", "procedure", "knowledge"]
        placeholders = ",".join("?" for _ in kinds)
        candidate_limit = max(limit * 25, 50)
        params: List[Any] = [*kinds, candidate_limit]
        cur = self._conn.cursor()
        cur.execute(
            f"""
            SELECT r.id, r.kind, r.key, r.content, r.metadata_json, r.created_at, r.updated_at,
                   e.vector_json, e.norm
            FROM memory_records r
            LEFT JOIN memory_embeddings e ON r.id = e.record_id
            WHERE r.kind IN ({placeholders})
            ORDER BY r.updated_at DESC
            LIMIT ?;
            """,
            params,
        )
        rows = cur.fetchall()
        q_vec, q_norm = _embed(q)
        now = time.time()
        scored: List[tuple[float, sqlite3.Row]] = []
        for r in rows:
            try:
                vec = json.loads(r["vector_json"]) if r["vector_json"] else None
                norm = float(r["norm"]) if r["norm"] else None
            except Exception:
                vec = None
                norm = None
            if not vec or not norm:
                try:
                    vec, norm = _embed(r["content"])
                    self._upsert_embedding(int(r["id"]), r["content"], now=now)
                except Exception:
                    vec, norm = None, None
            if vec and norm:
                dot = sum((qv * rv for qv, rv in zip(q_vec, vec)))
                cosine = dot / (q_norm * norm) if (q_norm and norm) else 0.0
            else:
                cosine = 0.0
            age = max(0.0, now - float(r["updated_at"]))
            recency = 1.0 / (1.0 + (age / 86400.0))
            score = (0.85 * cosine) + (0.15 * recency)
            scored.append((score, r))
        scored.sort(key=lambda x: x[0], reverse=True)
        out: List[MemoryRecord] = []
        for _, r in scored[: max(1, limit)]:
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
