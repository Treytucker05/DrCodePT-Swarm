from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import re
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

logger = logging.getLogger(__name__)

try:  # optional
    import faiss  # type: ignore

    _FAISS_AVAILABLE = True
except ImportError as exc:  # pragma: no cover - optional dependency
    logger.info("faiss not installed; vector search disabled: %s", exc)
    faiss = None  # type: ignore[assignment]
    _FAISS_AVAILABLE = False
except Exception as exc:  # pragma: no cover - optional dependency
    logger.warning("faiss import failed: %s", exc)
    faiss = None  # type: ignore[assignment]
    _FAISS_AVAILABLE = False


MemoryKind = Literal["experience", "procedure", "knowledge", "user_info"]

_FALLBACK_EMBED_DIM = 256
_DEFAULT_EMBED_MODEL = "all-MiniLM-L6-v2"
_EMBED_ENV_VAR = "AGENT_MEMORY_EMBED_MODEL"
_EMBED_BACKEND_ENV_VAR = "AGENT_MEMORY_EMBED_BACKEND"
_FAISS_DISABLE_ENV_VAR = "AGENT_MEMORY_FAISS_DISABLE"

_ST_MODEL = None
_ST_MODEL_NAME = None
_ST_MODEL_DIM = None
_ST_LOAD_ERROR = None


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", (text or "").lower())


def _hash_embed(text: str, dim: int = _FALLBACK_EMBED_DIM) -> tuple[List[float], float]:
    vec = [0.0] * dim
    for tok in _tokenize(text):
        h = int(hashlib.md5(tok.encode("utf-8", errors="replace")).hexdigest(), 16)
        idx = h % dim
        vec[idx] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return vec, norm


def _load_sentence_transformer():
    global _ST_MODEL, _ST_MODEL_NAME, _ST_MODEL_DIM, _ST_LOAD_ERROR
    if _ST_LOAD_ERROR is not None:
        return None
    if _ST_MODEL is not None:
        return _ST_MODEL
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:  # pragma: no cover - optional dependency
        logger.info("sentence-transformers not installed; using hash embeddings: %s", exc)
        _ST_LOAD_ERROR = exc
        return None
    except Exception as exc:  # pragma: no cover - optional dependency
        logger.warning("sentence-transformers import failed: %s", exc)
        _ST_LOAD_ERROR = exc
        return None
    model_name = (os.getenv(_EMBED_ENV_VAR) or _DEFAULT_EMBED_MODEL).strip()
    if not model_name:
        model_name = _DEFAULT_EMBED_MODEL
    try:
        _ST_MODEL = SentenceTransformer(model_name)
        _ST_MODEL_NAME = model_name
        try:
            _ST_MODEL_DIM = int(_ST_MODEL.get_sentence_embedding_dimension())
        except Exception:
            _ST_MODEL_DIM = None
    except (OSError, RuntimeError, ValueError) as exc:  # pragma: no cover - model download/load failure
        logger.warning("SentenceTransformer model load failed for '%s': %s", model_name, exc)
        _ST_LOAD_ERROR = exc
        _ST_MODEL = None
    except Exception as exc:  # pragma: no cover - unexpected failure
        logger.error("SentenceTransformer model load failed unexpectedly for '%s': %s", model_name, exc)
        _ST_LOAD_ERROR = exc
        _ST_MODEL = None
    return _ST_MODEL


def _embed(text: str) -> tuple[List[float], float, str, int]:
    backend = (os.getenv(_EMBED_BACKEND_ENV_VAR) or "").strip().lower()
    use_hash_only = backend in {"hash", "fallback", "simple"}
    if not use_hash_only:
        model = _load_sentence_transformer()
        if model is not None:
            vec = model.encode([text], normalize_embeddings=False)
            try:
                vec_list = vec[0].tolist()
            except Exception:
                vec_list = list(vec[0])
            dim = len(vec_list)
            norm = math.sqrt(sum(v * v for v in vec_list)) or 1.0
            model_name = _ST_MODEL_NAME or _DEFAULT_EMBED_MODEL
            return vec_list, norm, model_name, dim
    vec, norm = _hash_embed(text)
    return vec, norm, f"hash{_FALLBACK_EMBED_DIM}", _FALLBACK_EMBED_DIM


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
        self._faiss_index = None
        self._faiss_dim: Optional[int] = None
        self._faiss_model: Optional[str] = None
        self._init_schema()
        self._init_faiss_index()

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
        try:
            cols = {row[1] for row in cur.execute("PRAGMA table_info(memory_embeddings);").fetchall()}
            if "model" not in cols:
                cur.execute("ALTER TABLE memory_embeddings ADD COLUMN model TEXT;")
        except Exception:
            pass
        cur.execute("CREATE INDEX IF NOT EXISTS idx_memory_kind_updated ON memory_records(kind, updated_at DESC);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_memory_key ON memory_records(key);")
        self._conn.commit()

    def _init_faiss_index(self) -> None:
        if not _FAISS_AVAILABLE:
            return
        if os.getenv(_FAISS_DISABLE_ENV_VAR, "").strip().lower() in {"1", "true", "yes", "y"}:
            return
        try:
            _, _, model_name, dim = _embed(" ")
        except Exception:
            return
        try:
            index = faiss.IndexFlatIP(dim)  # type: ignore[attr-defined]
            self._faiss_index = faiss.IndexIDMap2(index)  # type: ignore[attr-defined]
            self._faiss_dim = dim
            self._faiss_model = model_name
            cur = self._conn.cursor()
            rows = cur.execute(
                "SELECT record_id, vector_json, norm, dim, model FROM memory_embeddings WHERE dim=?",
                (dim,),
            ).fetchall()
            ids: List[int] = []
            vecs: List[List[float]] = []
            for r in rows:
                if not r["vector_json"]:
                    continue
                if r["model"] and r["model"] != model_name:
                    continue
                try:
                    vec = json.loads(r["vector_json"])
                    norm = float(r["norm"]) if r["norm"] else None
                except Exception:
                    continue
                if not vec or not norm:
                    continue
                if norm != 0.0:
                    vec = [v / norm for v in vec]
                ids.append(int(r["record_id"]))
                vecs.append(vec)
            if ids:
                import numpy as np

                vec_arr = np.array(vecs, dtype="float32")
                id_arr = np.array(ids, dtype="int64")
                self._faiss_index.add_with_ids(vec_arr, id_arr)
        except Exception:
            self._faiss_index = None
            self._faiss_dim = None
            self._faiss_model = None

    def _update_faiss(self, record_id: int, vec: List[float], norm: float, model_name: str, dim: int) -> None:
        if self._faiss_index is None:
            return
        if self._faiss_dim != dim or self._faiss_model != model_name:
            return
        try:
            if norm != 0.0:
                vec = [v / norm for v in vec]
            import numpy as np

            vec_arr = np.array([vec], dtype="float32")
            id_arr = np.array([int(record_id)], dtype="int64")
            try:
                self._faiss_index.remove_ids(id_arr)
            except Exception:
                pass
            self._faiss_index.add_with_ids(vec_arr, id_arr)
        except Exception:
            pass

    def _upsert_embedding(self, record_id: int, content: str, *, now: Optional[float] = None) -> None:
        now = now or time.time()
        vec, norm, model_name, dim = _embed(content)
        cur = self._conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO memory_embeddings(record_id, dim, vector_json, norm, updated_at, model)
                VALUES(?, ?, ?, ?, ?, ?)
                ON CONFLICT(record_id) DO UPDATE SET
                  vector_json=excluded.vector_json,
                  norm=excluded.norm,
                  updated_at=excluded.updated_at,
                  dim=excluded.dim,
                  model=excluded.model;
                """,
                (record_id, dim, json.dumps(vec), float(norm), now, model_name),
            )
        except sqlite3.OperationalError:
            cur.execute(
                """
                INSERT INTO memory_embeddings(record_id, dim, vector_json, norm, updated_at)
                VALUES(?, ?, ?, ?, ?)
                ON CONFLICT(record_id) DO UPDATE SET
                  vector_json=excluded.vector_json,
                  norm=excluded.norm,
                  updated_at=excluded.updated_at,
                  dim=excluded.dim;
                """,
                (record_id, dim, json.dumps(vec), float(norm), now),
            )
        self._conn.commit()
        try:
            self._update_faiss(record_id, vec, norm, model_name, dim)
        except Exception:
            pass

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
        q_vec, q_norm, q_model, q_dim = _embed(q)
        now = time.time()

        if self._faiss_index is not None and q_dim == self._faiss_dim and q_model == self._faiss_model:
            try:
                import numpy as np

                qv = [v / q_norm for v in q_vec] if q_norm else q_vec
                k = max(limit * 5, limit)
                sims, ids = self._faiss_index.search(np.array([qv], dtype="float32"), k)
                id_list = [int(i) for i in ids[0] if int(i) >= 0]
                if id_list:
                    id_placeholders = ",".join("?" for _ in id_list)
                    rows = cur.execute(
                        f"""
                        SELECT id, kind, key, content, metadata_json, created_at, updated_at
                        FROM memory_records
                        WHERE id IN ({id_placeholders})
                        """,
                        id_list,
                    ).fetchall()
                    row_map = {int(r["id"]): r for r in rows}
                    scored: List[tuple[float, sqlite3.Row]] = []
                    for rank, rec_id in enumerate(id_list):
                        r = row_map.get(rec_id)
                        if r is None:
                            continue
                        sim = float(sims[0][rank])
                        age = max(0.0, now - float(r["updated_at"]))
                        recency = 1.0 / (1.0 + (age / 86400.0))
                        score = (0.85 * sim) + (0.15 * recency)
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
            except Exception:
                pass

        cur.execute(
            f"""
            SELECT r.id, r.kind, r.key, r.content, r.metadata_json, r.created_at, r.updated_at,
                   e.vector_json, e.norm, e.dim, e.model
            FROM memory_records r
            LEFT JOIN memory_embeddings e ON r.id = e.record_id
            WHERE r.kind IN ({placeholders})
            ORDER BY r.updated_at DESC
            LIMIT ?;
            """,
            params,
        )
        rows = cur.fetchall()
        scored: List[tuple[float, sqlite3.Row]] = []
        for r in rows:
            try:
                vec = json.loads(r["vector_json"]) if r["vector_json"] else None
                norm = float(r["norm"]) if r["norm"] else None
            except Exception:
                vec = None
                norm = None
            try:
                row_dim = int(r["dim"]) if r["dim"] else 0
            except Exception:
                row_dim = 0
            try:
                row_model = r["model"] if "model" in r.keys() else None
            except Exception:
                row_model = None
            dim_mismatch = row_dim and row_dim != q_dim
            model_mismatch = (row_model is not None and row_model != q_model)
            if not vec or not norm:
                try:
                    vec, norm, row_model, row_dim = _embed(r["content"])
                    self._upsert_embedding(int(r["id"]), r["content"], now=now)
                except Exception:
                    vec, norm = None, None
            elif dim_mismatch or model_mismatch:
                try:
                    vec, norm, row_model, row_dim = _embed(r["content"])
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
