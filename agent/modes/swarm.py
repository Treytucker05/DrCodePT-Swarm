from __future__ import annotations

import json
import hashlib
import logging
import os
import re
import time
import sys
import sqlite3
from dataclasses import dataclass, replace
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4
import traceback
from contextlib import contextmanager
from typing import Iterable

try:
    from tree_sitter_languages import get_parser
except Exception:  # pragma: no cover
    get_parser = None

from agent.autonomous.config import AgentConfig, PlannerConfig, RunnerConfig
from agent.autonomous.exceptions import AgentException
from agent.autonomous.models import SwarmResult
from agent.autonomous.isolation import (
    WorktreeInfo,
    copy_repo_to_workspace,
    create_worktree,
    remove_worktree,
    sanitize_branch_name,
)
from agent.autonomous.qa import QaResult, format_qa_summary, validate_artifacts
import subprocess
from agent.autonomous.manifest import write_run_manifest
from agent.preflight.repo_fish import PreflightResult, run_preflight
from agent.preflight.clarify import ClarifyResult, run_clarifier
from agent.autonomous.repo_scan import RepoScanner, is_repo_review_task
from agent.config.profile import resolve_profile
from agent.autonomous.runner import AgentRunner
from agent.autonomous.task_orchestrator import TaskOrchestrator
from agent.llm import CodexCliAuthError, CodexCliClient, CodexCliNotFoundError
from agent.llm import schemas as llm_schemas

logger = logging.getLogger(__name__)


_CODEX_CONFIG_CACHE: dict | None = None


def _load_codex_config() -> dict:
    global _CODEX_CONFIG_CACHE
    if _CODEX_CONFIG_CACHE is not None:
        return _CODEX_CONFIG_CACHE
    path = Path.home() / ".codex" / "config.toml"
    if not path.is_file():
        _CODEX_CONFIG_CACHE = {}
        return _CODEX_CONFIG_CACHE
    raw = ""
    try:
        raw = path.read_text(encoding="utf-8", errors="ignore")
        try:
            import tomllib  # type: ignore

            _CODEX_CONFIG_CACHE = tomllib.loads(raw)
            return _CODEX_CONFIG_CACHE or {}
        except Exception:
            pass
    except Exception:
        _CODEX_CONFIG_CACHE = {}
        return _CODEX_CONFIG_CACHE

    cfg: dict[str, str] = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("["):
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key in {"model", "model_reasoning_effort"}:
            cfg[key] = value
    _CODEX_CONFIG_CACHE = cfg
    return _CODEX_CONFIG_CACHE


def _normalize_effort(value: str) -> str:
    effort = (value or "").strip().lower()
    if effort in {"xhigh", "extra_high", "xh"}:
        return "high"
    if effort in {"xlow", "extra_low", "xl"}:
        return "low"
    if effort in {"high", "medium", "low"}:
        return effort
    return "medium"


def _debug_agent_banner(agent_label: str) -> None:
    cfg = _load_codex_config() or {}
    profiles = cfg.get("profiles") if isinstance(cfg.get("profiles"), dict) else {}
    profile_name = (os.getenv("CODEX_PROFILE_REASON") or "reason").strip()
    profile_cfg = profiles.get(profile_name, {}) if isinstance(profiles, dict) else {}
    model = (os.getenv("CODEX_MODEL") or profile_cfg.get("model") or cfg.get("model") or "default").strip()
    effort_raw = os.getenv("CODEX_REASONING_EFFORT") or profile_cfg.get("model_reasoning_effort") or cfg.get("model_reasoning_effort") or "medium"
    effort = _normalize_effort(str(effort_raw))
    print(f"[MODEL: {model} | EFFORT: {effort} | AGENT: {agent_label}]")


def _current_model_effort() -> tuple[str, str]:
    cfg = _load_codex_config() or {}
    profiles = cfg.get("profiles") if isinstance(cfg.get("profiles"), dict) else {}
    profile_name = (os.getenv("CODEX_PROFILE_REASON") or "reason").strip()
    profile_cfg = profiles.get(profile_name, {}) if isinstance(profiles, dict) else {}
    model = (os.getenv("CODEX_MODEL") or profile_cfg.get("model") or cfg.get("model") or "default").strip()
    effort_raw = os.getenv("CODEX_REASONING_EFFORT") or profile_cfg.get("model_reasoning_effort") or cfg.get("model_reasoning_effort") or "medium"
    effort = _normalize_effort(str(effort_raw))
    return model, effort


def _agent_log_dir(repo_root: Path) -> Path:
    return repo_root / "agent" / "logs"


def _write_agent_log(repo_root: Path, agent_name: str, payload: dict) -> None:
    log_dir = _agent_log_dir(repo_root)
    log_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe = re.sub(r"[^a-zA-Z0-9_-]+", "_", agent_name.strip().lower())
    path = log_dir / f"{safe}_{ts}.json"
    payload["timestamp"] = datetime.now(timezone.utc).isoformat()
    try:
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def _compress_prompt(prompt: str, *, max_chars: int | None = None) -> str:
    if not prompt:
        return prompt
    lines = [ln.rstrip() for ln in prompt.strip().splitlines()]
    compact: list[str] = []
    blank = False
    for line in lines:
        if not line.strip():
            if not blank:
                compact.append("")
            blank = True
            continue
        blank = False
        compact.append(line)
    text = "\n".join(compact)
    if max_chars and len(text) > max_chars:
        return text[:max_chars]
    return text


def _resolve_repo_hash(repo_root: Path) -> str:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if proc.returncode == 0:
            return (proc.stdout or "").strip() or "unknown"
    except Exception:
        pass
    # Fallback: hash top-level listing + mtimes
    try:
        items = []
        for path in sorted(repo_root.iterdir(), key=lambda p: p.name):
            try:
                stat = path.stat()
                items.append(f"{path.name}:{stat.st_mtime}:{stat.st_size}")
            except Exception:
                items.append(path.name)
        return hashlib.sha256("|".join(items).encode("utf-8")).hexdigest()
    except Exception:
        return "unknown"


def _git_changed_files(repo_root: Path) -> list[Path]:
    files: set[str] = set()
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if proc.returncode == 0:
            for line in (proc.stdout or "").splitlines():
                line = line.strip()
                if not line:
                    continue
                path = line[3:].strip() if len(line) >= 4 else line
                if "->" in path:
                    path = path.split("->", 1)[1].strip()
                if path:
                    files.add(path)
    except Exception:
        pass
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "diff", "--name-only", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if proc.returncode == 0:
            for line in (proc.stdout or "").splitlines():
                path = line.strip()
                if path:
                    files.add(path)
    except Exception:
        pass
    resolved: list[Path] = []
    for rel in sorted(files):
        path = (repo_root / rel).resolve()
        if path.is_file():
            resolved.append(path)
    return resolved


def _file_hash(path: Path) -> str:
    try:
        data = path.read_bytes()
    except Exception:
        return "unreadable"
    return hashlib.sha256(data).hexdigest()


def _collect_file_hashes(paths: list[Path]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in paths:
        try:
            rel = str(path)
            hashes[rel] = _file_hash(path)
        except Exception:
            continue
    return hashes


def _hash_agent_input(agent: str, file_hashes: dict[str, str], extra: dict | None = None) -> str:
    payload = {
        "agent": agent,
        "files": file_hashes,
        "extra": extra or {},
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _open_analysis_db(repo_root: Path) -> sqlite3.Connection | None:
    try:
        db_path = repo_root / "agent" / "past_analyses.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(db_path)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_cache (
                agent TEXT NOT NULL,
                input_hash TEXT NOT NULL,
                repo_hash TEXT NOT NULL,
                file_hashes TEXT NOT NULL,
                output TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (agent, input_hash)
            )
            """
        )
        return conn
    except Exception:
        return None


def _cache_lookup(conn: sqlite3.Connection | None, agent: str, input_hash: str) -> str | None:
    if conn is None:
        return None
    try:
        cur = conn.execute(
            "SELECT output FROM agent_cache WHERE agent = ? AND input_hash = ?",
            (agent, input_hash),
        )
        row = cur.fetchone()
        return row[0] if row else None
    except Exception:
        return None


def _cache_store(
    conn: sqlite3.Connection | None,
    *,
    agent: str,
    input_hash: str,
    repo_hash: str,
    file_hashes: dict,
    output: str,
) -> None:
    if conn is None:
        return
    try:
        conn.execute(
            "INSERT OR REPLACE INTO agent_cache(agent, input_hash, repo_hash, file_hashes, output, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (
                agent,
                input_hash,
                repo_hash,
                json.dumps(file_hashes, ensure_ascii=False),
                output,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
    except Exception:
        return


_AST_PARSER_CACHE: dict[str, Any] = {}
_AST_LANG_BY_EXT = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".cs": "c_sharp",
    ".rb": "ruby",
    ".php": "php",
}
_AST_IMPORT_NODES = {
    "import_statement",
    "import_from_statement",
    "import_declaration",
    "using_declaration",
    "include_directive",
    "require_call",
}
_AST_FUNCTION_NODES = {
    "function_definition",
    "function_declaration",
    "method_definition",
}
_AST_CLASS_NODES = {
    "class_definition",
    "class_declaration",
}


def _simple_repo_roles(kind: str) -> list[str]:
    kind = (kind or "").strip().lower()
    if kind in {"gap_analysis", "gaps"}:
        return ["Gap Analysis", "Coverage & Testing Gaps", "Quick Wins"]
    if kind in {"architecture_review", "architecture"}:
        return ["Architecture Review", "Dependency Boundaries", "Risk Hotspots"]
    if kind in {"documentation", "docs"}:
        return ["Documentation Gaps", "Onboarding Clarity", "Quick Wins"]
    if kind in {"code_search"}:
        return ["Code Search", "Where It Lives", "Quick Pointers"]
    return ["Gap Analysis", "Architecture Review", "Quick Wins"]


def _role_focus_instructions(role: str) -> str:
    role_lower = (role or "").lower()
    if "gap analysis" in role_lower:
        return (
            "Scan for TODO/FIXME comments, incomplete implementations, "
            "missing error handling, and risky assumptions."
        )
    if "coverage" in role_lower or "testing" in role_lower:
        return (
            "Scan for missing test files, low coverage indicators, CI/CD configuration gaps, "
            "missing test assertions, and untested critical paths. Skip observation and go "
            "straight to analysis."
        )
    if "quick wins" in role_lower:
        return (
            "Find easy improvements: typos, unused imports, obvious refactors, "
            "outdated dependencies, or small cleanup tasks."
        )
    if "architecture" in role_lower:
        return "Review architecture boundaries, module coupling, and layering issues."
    if "dependency" in role_lower or "risk" in role_lower:
        return "Identify dependency or integration risks and high-risk areas."
    if "documentation" in role_lower:
        return "Identify missing or outdated documentation and onboarding gaps."
    if "code search" in role_lower or "where it lives" in role_lower:
        return "Locate likely file paths and entry points for the requested area."
    return "Provide focused findings relevant to your role."


def _find_key_docs(repo_root: Path) -> dict:
    targets = ["README.md", "README.txt", "ARCHITECTURE.md", "ENHANCEMENT_SUMMARY.md"]
    found: dict[str, Path] = {}
    for name in targets:
        direct = repo_root / name
        if direct.is_file():
            found[name] = direct
    if len(found) < len(targets):
        # Case-insensitive fallback search (shallow)
        try:
            for path in repo_root.rglob("*.md"):
                if path.name.upper() in {t.upper() for t in targets}:
                    found[path.name] = path
        except Exception:
            pass
    return found


def _read_text_snippet(path: Path, *, max_chars: int = 6000) -> str:
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
        return _sanitize_doc_text(raw)[:max_chars]
    except Exception:
        return ""


def _extract_bullets(section: str) -> list[str]:
    bullets: list[str] = []
    for line in section.splitlines():
        ln = line.strip()
        if ln.startswith("- "):
            bullets.append(ln[2:].strip())
    return bullets


def _extract_section(text: str, header: str) -> str:
    lines = text.splitlines()
    header_lower = header.lower()
    capture = False
    buf: list[str] = []
    for line in lines:
        raw = line.strip()
        if raw.lower().startswith(header_lower):
            capture = True
            continue
        if capture and raw.endswith(":") and raw[:-1].strip().isupper():
            break
        if capture:
            buf.append(line)
    return "\n".join(buf).strip()


@contextmanager
def _temporary_reasoning_effort(effort: str | None):
    prev = os.environ.get("CODEX_REASONING_EFFORT")
    if effort:
        os.environ["CODEX_REASONING_EFFORT"] = effort
    try:
        yield
    finally:
        if prev is None:
            os.environ.pop("CODEX_REASONING_EFFORT", None)
        else:
            os.environ["CODEX_REASONING_EFFORT"] = prev


@contextmanager
def _temporary_env_var(name: str, value: str | None):
    prev = os.environ.get(name)
    if value is None:
        os.environ.pop(name, None)
    else:
        os.environ[name] = value
    try:
        yield
    finally:
        if prev is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = prev


def _extract_gap_topics(text: str, *, limit: int = 6) -> list[str]:
    topics: list[str] = []
    for line in text.splitlines():
        raw = line.strip()
        if not raw.startswith("-"):
            continue
        item = raw.lstrip("-").strip()
        if not item:
            continue
        topic = item.split(":")[0].strip()
        if topic and topic.lower() not in {t.lower() for t in topics}:
            topics.append(topic)
        if len(topics) >= limit:
            break
    return topics


def _scan_todos(
    repo_root: Path,
    repo_map: list,
    *,
    limit: int = 40,
    focus_files: set[Path] | None = None,
) -> str:
    hits: list[str] = []
    for entry in repo_map:
        path = Path(getattr(entry, "path", ""))
        name = path.name.upper()
        if name in {"AGENTS.MD", "CONTINUITY.MD", "CONTINUITY-POWERHOUSEATX.MD"}:
            continue
        if not path.is_file():
            continue
        if focus_files is not None:
            try:
                if path.resolve() not in focus_files:
                    continue
            except Exception:
                continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for line in text.splitlines():
            if any(tag in line for tag in ("TODO", "FIXME", "XXX")):
                hits.append(f"{path}: {line.strip()[:200]}")
                if len(hits) >= limit:
                    return "\n".join(f"- {h}" for h in hits)
    return "\n".join(f"- {h}" for h in hits)


def _get_tree_sitter_parser(language: str) -> Any:
    if not language:
        return None
    if language in _AST_PARSER_CACHE:
        return _AST_PARSER_CACHE[language]
    if get_parser is None:
        _AST_PARSER_CACHE[language] = None
        return None
    try:
        parser = get_parser(language)
    except Exception:
        parser = None
    _AST_PARSER_CACHE[language] = parser
    return parser


def _node_text(node: Any, source: bytes, *, limit: int = 140) -> str:
    text = source[node.start_byte : node.end_byte].decode("utf-8", errors="ignore")
    text = " ".join(text.split())
    return text[:limit]


def _node_name(node: Any, source: bytes) -> str:
    name_node = getattr(node, "child_by_field_name", lambda *_: None)("name")
    if name_node is None:
        return ""
    return _node_text(name_node, source, limit=80)


def _should_skip_ast_path(path: Path) -> bool:
    skip_parts = {
        ".git",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        "site-packages",
        "dist",
        "build",
        "coverage",
        ".pytest_cache",
    }
    for part in path.parts:
        if part in skip_parts:
            return True
    return False


def _extract_ast_summary(
    repo_root: Path,
    repo_map: list,
    *,
    focus_files: set[Path] | None = None,
    max_files: int = 60,
    max_bytes: int = 220_000,
    max_items: int = 10,
) -> str:
    if get_parser is None:
        return "- AST parsing unavailable (tree-sitter-languages not installed)"

    lines: list[str] = []
    for entry in repo_map:
        raw_path = Path(getattr(entry, "path", ""))
        path = raw_path if raw_path.is_absolute() else (repo_root / raw_path)
        if not path.is_file():
            continue
        if focus_files is not None:
            try:
                if path.resolve() not in focus_files:
                    continue
            except Exception:
                continue
        if _should_skip_ast_path(path):
            continue
        suffix = path.suffix.lower()
        language = _AST_LANG_BY_EXT.get(suffix)
        if not language:
            continue
        try:
            if path.stat().st_size > max_bytes:
                continue
        except Exception:
            continue
        parser = _get_tree_sitter_parser(language)
        if parser is None:
            continue
        try:
            source = path.read_bytes()
        except Exception:
            continue

        try:
            tree = parser.parse(source)
        except Exception:
            continue

        imports: list[str] = []
        functions: list[str] = []
        classes: list[str] = []
        seen_imports: set[str] = set()
        seen_functions: set[str] = set()
        seen_classes: set[str] = set()

        stack = [tree.root_node]
        while stack:
            node = stack.pop()
            ntype = getattr(node, "type", "")
            if ntype in _AST_IMPORT_NODES and len(imports) < max_items:
                text = _node_text(node, source)
                if text and text not in seen_imports:
                    imports.append(text)
                    seen_imports.add(text)
            if ntype in _AST_FUNCTION_NODES and len(functions) < max_items:
                name = _node_name(node, source) or _node_text(node, source, limit=80)
                if name and name not in seen_functions:
                    functions.append(name)
                    seen_functions.add(name)
            if ntype in _AST_CLASS_NODES and len(classes) < max_items:
                name = _node_name(node, source) or _node_text(node, source, limit=80)
                if name and name not in seen_classes:
                    classes.append(name)
                    seen_classes.add(name)
            if len(imports) >= max_items and len(functions) >= max_items and len(classes) >= max_items:
                continue
            stack.extend(reversed(getattr(node, "children", []) or []))

        if not imports and not functions and not classes:
            continue

        try:
            rel = str(path.resolve().relative_to(repo_root))
        except Exception:
            rel = str(path)
        parts: list[str] = []
        if imports:
            parts.append(f"imports: {', '.join(imports)}")
        if functions:
            parts.append(f"functions: {', '.join(functions)}")
        if classes:
            parts.append(f"classes: {', '.join(classes)}")
        if parts:
            lines.append(f"- {rel}: " + "; ".join(parts))
        if len(lines) >= max_files:
            break

    return "\n".join(lines) if lines else "- (no AST summary available)"


def _find_dependent_files(
    repo_root: Path,
    repo_map: list,
    changed_files: list[Path],
    *,
    max_files: int = 200,
    max_bytes: int = 120_000,
) -> list[Path]:
    if not changed_files:
        return []
    stems = {p.stem for p in changed_files if p.stem}
    if not stems:
        return []
    patterns = [
        re.compile(rf"\\bimport\\s+{re.escape(stem)}\\b") for stem in stems
    ] + [
        re.compile(rf"\\bfrom\\s+{re.escape(stem)}\\b") for stem in stems
    ] + [
        re.compile(rf"\\brequire\\(\\s*[\\\"\\']{re.escape(stem)}[\\\"\\']\\s*\\)")
        for stem in stems
    ] + [
        re.compile(rf"\\bfrom\\s+[\\\"\\']{re.escape(stem)}[\\\"\\']") for stem in stems
    ]
    dependents: list[Path] = []
    changed_set = {p.resolve() for p in changed_files if p.is_file()}
    for entry in repo_map:
        raw_path = Path(getattr(entry, "path", ""))
        path = raw_path if raw_path.is_absolute() else (repo_root / raw_path)
        if not path.is_file():
            continue
        try:
            resolved = path.resolve()
        except Exception:
            continue
        if resolved in changed_set:
            continue
        if _should_skip_ast_path(path):
            continue
        try:
            if path.stat().st_size > max_bytes:
                continue
        except Exception:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if any(p.search(text) for p in patterns):
            dependents.append(resolved)
        if len(dependents) >= max_files:
            break
    return dependents


def _restricted_env(repo_root: Path, run_root: Path) -> dict:
    # Rule of Two: minimize env exposure (no secrets) and redirect caches away from the repo.
    tmp_dir = run_root / "dynamic_tmp"
    pycache_dir = run_root / "dynamic_pycache"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    pycache_dir.mkdir(parents=True, exist_ok=True)

    return {
        "PATH": os.environ.get("PATH", ""),
        "SystemRoot": os.environ.get("SystemRoot", "C:\\Windows"),
        "WINDIR": os.environ.get("WINDIR", "C:\\Windows"),
        "COMSPEC": os.environ.get("COMSPEC", "C:\\Windows\\System32\\cmd.exe"),
        "PATHEXT": os.environ.get("PATHEXT", ""),
        "PYTHONPATH": str(repo_root),
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPYCACHEPREFIX": str(pycache_dir),
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "PIP_DISABLE_PIP_VERSION_CHECK": "1",
        "TMP": str(tmp_dir),
        "TEMP": str(tmp_dir),
        "TMPDIR": str(tmp_dir),
        "HOME": str(run_root),
        "USERPROFILE": str(run_root),
        "APPDATA": str(run_root),
        "LOCALAPPDATA": str(run_root),
        "PYTHONHASHSEED": "0",
    }


def _run_dynamic_checks(repo_root: Path, run_root: Path) -> str:
    # Rule of Two: read-only intent (no repo writes) with restricted env and redirected caches.
    lines: list[str] = []
    env = _restricted_env(repo_root, run_root)
    packages = []
    try:
        for path in repo_root.iterdir():
            if path.is_dir() and (path / "__init__.py").is_file():
                packages.append(path.name)
    except Exception:
        packages = []
    for pkg in packages[:3]:
        cmd = [sys.executable, "-c", f"import {pkg}; print('{pkg} OK')"]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=str(repo_root),
                env=env,
            )
            if proc.returncode == 0:
                lines.append(f"- import {pkg}: OK")
            else:
                lines.append(f"- import {pkg}: FAIL ({proc.stderr.strip()[:200]})")
        except Exception as exc:
            lines.append(f"- import {pkg}: ERROR ({exc})")

    test_candidates = [
        repo_root / "tests",
        repo_root / "pytest.ini",
        repo_root / "pyproject.toml",
    ]
    if any(p.exists() for p in test_candidates):
        cache_dir = run_root / "pytest_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        basetemp = run_root / "pytest_tmp"
        basetemp.mkdir(parents=True, exist_ok=True)
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "--maxfail=1",
            "-p",
            "no:cacheprovider",
            "-o",
            f"cache_dir={cache_dir}",
            "--basetemp",
            str(basetemp),
        ]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=45,
                cwd=str(repo_root),
                env=env,
            )
            out = (proc.stdout or "").strip()
            err = (proc.stderr or "").strip()
            lines.append(f"- pytest exit={proc.returncode}")
            if out:
                lines.append(f"  stdout: {out[:500]}")
            if err:
                lines.append(f"  stderr: {err[:500]}")
        except Exception as exc:
            lines.append(f"- pytest: ERROR ({exc})")
    else:
        lines.append("- pytest: SKIPPED (no obvious test config found)")

    return "\n".join(lines)


def _is_incomplete_observation(output: str) -> bool:
    if not output:
        return False
    text = output.strip().lower()
    if text in {"phase: observe", "phase:observe", "observe"}:
        return True
    lines = [ln.strip().lower() for ln in output.splitlines() if ln.strip()]
    if len(lines) == 1 and lines[0].startswith("phase: observe"):
        return True
    joined = " ".join(lines)
    if "observe" in joined and "now" in joined and "scanning" in joined:
        return True
    return False


def _parse_reanalysis(text: str) -> dict[str, str]:
    requests: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip().lower().startswith("reanalyze"):
            continue
        _, rest = line.split(":", 1) if ":" in line else ("", "")
        if "->" in rest:
            agent, guidance = rest.split("->", 1)
            agent = agent.strip().title()
            requests[agent] = guidance.strip()
    return requests


def _parse_confidence_lines(text: str) -> list[dict]:
    results: list[dict] = []
    score_re = re.compile(r"\b(static|dynamic|research|avg)\s*=\s*([01](?:\.\d+)?)", re.IGNORECASE)
    for line in text.splitlines():
        if "gap:" not in line.lower():
            continue
        gap = ""
        if "gap:" in line.lower():
            try:
                gap = line.split("gap:", 1)[1].split("|", 1)[0].strip()
            except Exception:
                gap = line.strip()
        scores: dict[str, float] = {}
        for key, value in score_re.findall(line):
            try:
                scores[key.lower()] = float(value)
            except ValueError:
                continue
        raw_scores = [v for k, v in scores.items() if k != "avg"]
        avg = scores.get("avg")
        if avg is None and raw_scores:
            avg = sum(raw_scores) / max(len(raw_scores), 1)
        variance = None
        if len(raw_scores) >= 2:
            variance = max(raw_scores) - min(raw_scores)
        results.append(
            {
                "gap": gap or line.strip(),
                "scores": scores,
                "avg": avg,
                "variance": variance,
            }
        )
    return results


def _confidence_stats(gaps: list[dict]) -> tuple[float | None, dict[str, float], list[dict]]:
    avg_values = [g["avg"] for g in gaps if isinstance(g.get("avg"), (int, float))]
    global_avg = sum(avg_values) / len(avg_values) if avg_values else None
    agent_scores: dict[str, list[float]] = {"static": [], "dynamic": [], "research": []}
    for g in gaps:
        scores = g.get("scores") or {}
        for agent in agent_scores:
            if agent in scores:
                agent_scores[agent].append(scores[agent])
    agent_avgs: dict[str, float] = {
        agent: (sum(vals) / len(vals)) for agent, vals in agent_scores.items() if vals
    }
    uncertain = [g for g in gaps if g.get("variance") is not None and g["variance"] > 0.5]
    return global_avg, agent_avgs, uncertain


def _extract_repo_kind(objective: str) -> str:
    text = (objective or "").strip()
    match = re.match(r"^\[REPO MODE:\s*([^\]]+)\]", text, flags=re.IGNORECASE)
    if not match:
        return ""
    kind = match.group(1).strip().lower().replace(" ", "_")
    return kind


def _format_repo_map(repo_root: Path, repo_map: list) -> str:
    lines: list[str] = []
    for entry in repo_map:
        path = getattr(entry, "path", "") or ""
        name = Path(path).name
        if name.upper() in {"AGENTS.md".upper(), "CONTINUITY.md".upper(), "CONTINUITY-POWERHOUSEATX.MD"}:
            continue
        desc = getattr(entry, "description", "") or ""
        try:
            rel = str(Path(path).resolve().relative_to(repo_root))
        except Exception:
            rel = path
        if desc:
            lines.append(f"- {rel}: {desc}")
        else:
            lines.append(f"- {rel}")
        if len(lines) >= 30:
            break
    return "\n".join(lines)


def _sanitize_doc_text(text: str) -> str:
    if not text:
        return text
    deny = ("continuity.md", "agents.md", "continuity ledger", "workspace rules")
    cleaned_lines = []
    for line in text.splitlines():
        lower = line.lower()
        if any(token in lower for token in deny):
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines)


def _repo_access_instruction() -> str:
    return "Analyze the repository directly.\nDo NOT ask for permission.\n"


def _workspace_override() -> str:
    return (
        "WORKSPACE OVERRIDE - READ THIS FIRST:\n"
        "You are NOT operating in a standard Codex workspace.\n"
        "Do NOT read CONTINUITY.md or any workspace files.\n"
        "Do NOT request workspace confirmation or ledger updates.\n"
        "Do NOT mention \"UNCONFIRMED\" or \"need to read CONTINUITY.md\".\n"
        "You have complete information in this prompt.\n"
        "Proceed directly with your analysis task.\n"
    )


def mode_swarm_simple(
    objective: str,
    *,
    unsafe_mode: bool = False,
    profile: str | None = None,
    max_agents: int | None = None,
    timeout_seconds: int | None = None,
) -> None:
    """Simple swarm: deep repo analysis with supervisor/critic/synthesis."""
    _load_dotenv()
    repo_root = Path(__file__).resolve().parents[2]
    run_root = repo_root / "runs" / "swarm_simple" / datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    # Rule of Two: analysis is read-only; all generated artifacts stay under runs/swarm_simple.
    run_root.mkdir(parents=True, exist_ok=True)

    repo_hash = _resolve_repo_hash(repo_root)
    analysis_db = _open_analysis_db(repo_root)
    prompt_max_chars = _int_env("SWARM_SIMPLE_PROMPT_MAX_CHARS", 12000)
    docs_max_chars = _int_env("SWARM_SIMPLE_DOCS_MAX_CHARS", 3500)
    dependent_limit = _int_env("SWARM_SIMPLE_DEPENDENT_SCAN_LIMIT", 200)
    max_output_defaults = {
        "Fingerprint": 300,
        "ProblemModel": 400,
        "Supervisor": 120,
        "Static": 500,
        "Dynamic": 500,
        "Research": 600,
        "Critic": 500,
        "Synthesis": 800,
    }

    profile_cfg = resolve_profile(profile, env_keys=("SWARM_SIMPLE_PROFILE", "SWARM_PROFILE", "AUTO_PROFILE", "AGENT_PROFILE"))
    max_agents = max_agents or 3

    # Timing + reasoning layers
    timeout_fingerprint = None
    timeout_static = None
    timeout_dynamic = None
    timeout_research = None
    timeout_supervisor = None
    timeout_critic = None
    timeout_synthesis = None

    scan_dir = run_root / "repo_scan"
    scanner = RepoScanner(
        repo_root=repo_root,
        run_dir=scan_dir,
        max_results=min(profile_cfg.max_glob_results, 200),
        profile=profile_cfg,
        usage=None,
    )
    _, repo_map = scanner.scan()

    root_entries = []
    try:
        root_entries = sorted([p.name for p in repo_root.iterdir()])[:40]
    except Exception:
        root_entries = []

    changed_files = _git_changed_files(repo_root)
    dependent_files: list[Path] = []
    if changed_files:
        dependent_files = _find_dependent_files(
            repo_root,
            repo_map,
            changed_files,
            max_files=dependent_limit,
        )
    focus_files = changed_files + [p for p in dependent_files if p not in changed_files]
    focus_files_set = {p.resolve() for p in focus_files if p.is_file()}
    if focus_files:
        print(f"[SWARM SIMPLE] Incremental focus: {len(changed_files)} changed, {len(dependent_files)} dependents")
    else:
        print("[SWARM SIMPLE] Incremental focus: none (full scan)")

    ast_summary = _extract_ast_summary(
        repo_root,
        repo_map,
        focus_files=focus_files_set if focus_files else None,
        max_files=_int_env("SWARM_SIMPLE_AST_MAX_FILES", 60),
        max_items=_int_env("SWARM_SIMPLE_AST_MAX_ITEMS", 10),
    )
    roles = ["Static", "Dynamic", "Research"]

    print("\n[SWARM SIMPLE] Objective:", objective)
    print("[SWARM SIMPLE] Agents:", ", ".join(roles + ["Critic", "Synthesis"]))

    def _max_tokens_for(label: str) -> int:
        key = f"SWARM_SIMPLE_MAX_TOKENS_{label.upper()}"
        raw = os.getenv(key) or os.getenv("SWARM_SIMPLE_MAX_TOKENS")
        if raw:
            try:
                return max(50, int(raw))
            except ValueError:
                pass
        return max_output_defaults.get(label, 400)

    def _output_limit_note(label: str) -> str:
        tokens = _max_tokens_for(label)
        words = max(40, int(tokens * 0.75))
        return f"Keep the response under ~{tokens} tokens (~{words} words)."

    def _call_llm(
        label: str,
        prompt: str,
        *,
        effort: str,
        timeout: int | None,
        log_name: str,
        cached_output: str | None = None,
        cache_meta: dict | None = None,
        enable_search: bool = False,
    ) -> str:
        started = time.monotonic()
        compressed = _compress_prompt(prompt, max_chars=prompt_max_chars)
        if cached_output is not None:
            duration = time.monotonic() - started
            model, effort_used = _current_model_effort()
            _write_agent_log(
                repo_root,
                label,
                {
                    "agent": label,
                    "status": "cached",
                    "duration_sec": round(duration, 2),
                    "model": model,
                    "effort": effort_used,
                    "prompt_chars": len(compressed),
                    "response_chars": len(cached_output),
                    "usage": None,
                    "tokens": None,
                    "cached": True,
                    "cache_meta": cache_meta or {},
                },
            )
            return cached_output
        with _temporary_reasoning_effort(effort), _temporary_env_var(
            "CODEX_ENABLE_WEB_SEARCH", "1" if enable_search else None
        ):
            _debug_agent_banner(label)
            llm = CodexCliClient.from_env(workdir=repo_root, log_dir=run_root / log_name)
            data = llm.reason_json(compressed, schema_path=llm_schemas.CHAT_RESPONSE, timeout_seconds=timeout)
        response = (data.get("response") or "").strip()
        duration = time.monotonic() - started
        model, effort_used = _current_model_effort()
        usage = data.get("usage") if isinstance(data, dict) else None
        tokens = None
        if isinstance(usage, dict):
            tokens = (
                usage.get("total_tokens")
                or usage.get("output_tokens")
                or usage.get("completion_tokens")
            )
        _write_agent_log(
            repo_root,
            label,
            {
                "agent": label,
                "status": "success",
                "duration_sec": round(duration, 2),
                "model": model,
                "effort": effort_used,
                "prompt_chars": len(compressed),
                "response_chars": len(response),
                "usage": usage,
                "tokens": tokens,
                "cached": False,
                "cache_meta": cache_meta or {},
            },
        )
        return response

    # Fingerprint extraction
    docs = _find_key_docs(repo_root)
    docs_block = []
    for name, path in docs.items():
        content = _read_text_snippet(path, max_chars=docs_max_chars)
        if content:
            docs_block.append(f"## {name}\n{content}")
    docs_text = "\n\n".join(docs_block).strip()

    fingerprint_prompt = (
        _workspace_override()
        + "You are the Fingerprint Extractor.\n"
        "Extract system claims from README/docs and promises from ARCHITECTURE.\n"
        "Create a verification checklist.\n"
        "Return sections:\n"
        "SUMMARY:\n- ...\n"
        "CLAIMS:\n- ...\n"
        "PROMISES:\n- ...\n"
        "CHECKLIST:\n- ...\n"
        f"{_output_limit_note('Fingerprint')}\n"
        "Use only the provided docs. Do NOT ask for permission.\n"
        f"Objective: {objective}\n\n"
        f"Docs:\n{docs_text}\n"
    )
    fingerprint_files = list(docs.values())
    fingerprint_hashes = _collect_file_hashes(fingerprint_files)
    fingerprint_input_hash = _hash_agent_input(
        "Fingerprint",
        fingerprint_hashes,
        {"objective": objective, "repo_hash": repo_hash},
    )
    fingerprint_cached = _cache_lookup(analysis_db, "Fingerprint", fingerprint_input_hash)
    fingerprint_text = _call_llm(
        "Fingerprint",
        fingerprint_prompt,
        effort="low",
        timeout=timeout_fingerprint,
        log_name="fingerprint",
        cached_output=fingerprint_cached,
        cache_meta={"input_hash": fingerprint_input_hash, "repo_hash": repo_hash},
    )
    if fingerprint_cached is None:
        _cache_store(
            analysis_db,
            agent="Fingerprint",
            input_hash=fingerprint_input_hash,
            repo_hash=repo_hash,
            file_hashes=fingerprint_hashes,
            output=fingerprint_text,
        )
    claims = _extract_bullets(_extract_section(fingerprint_text, "CLAIMS"))
    promises = _extract_bullets(_extract_section(fingerprint_text, "PROMISES"))
    checklist = _extract_bullets(_extract_section(fingerprint_text, "CHECKLIST"))

    fingerprint_digest = hashlib.sha256(fingerprint_text.encode("utf-8", errors="ignore")).hexdigest()
    problem_model_prompt = (
        _workspace_override()
        + "You are the Problem Modeler for Model-First Reasoning.\n"
        "Build an explicit shared problem model BEFORE any reasoning.\n"
        "Define what counts as a gap, evidence requirements, scope, constraints, and success criteria.\n"
        "Return sections:\n"
        "MODEL:\n- Scope: ...\n- Claims: ...\n- Gap Criteria: ...\n- Evidence Rules: ...\n- Checklist: ...\n- Unknowns: ...\n"
        f"{_output_limit_note('ProblemModel')}\n"
        f"Objective: {objective}\n"
        f"Fingerprint:\n{fingerprint_text}\n"
    )
    problem_model_input_hash = _hash_agent_input(
        "ProblemModel",
        fingerprint_hashes,
        {"objective": objective, "repo_hash": repo_hash, "fingerprint": fingerprint_digest},
    )
    problem_model_cached = _cache_lookup(analysis_db, "ProblemModel", problem_model_input_hash)
    problem_model_text = _call_llm(
        "ProblemModel",
        problem_model_prompt,
        effort="low",
        timeout=timeout_fingerprint,
        log_name="problem_model",
        cached_output=problem_model_cached,
        cache_meta={"input_hash": problem_model_input_hash, "repo_hash": repo_hash},
    )
    if problem_model_cached is None:
        _cache_store(
            analysis_db,
            agent="ProblemModel",
            input_hash=problem_model_input_hash,
            repo_hash=repo_hash,
            file_hashes=fingerprint_hashes,
            output=problem_model_text,
        )

    def _supervisor_check(role: str, output: str) -> tuple[bool, str]:
        prompt = (
            _workspace_override()
            + "You are the Supervisor QA-Checker.\n"
            "Determine if the agent stayed on-topic for repo gap analysis.\n"
            "Respond with either:\n"
            "OK\n"
            "or\n"
            "REDIRECT: <one-sentence guidance to refocus>\n\n"
            f"{_output_limit_note('Supervisor')}\n"
            f"Objective: {objective}\n"
            f"Problem Model:\n{problem_model_text}\n"
            f"Agent: {role}\n"
            f"Output:\n{output}\n"
        )
        resp = _call_llm(
            "Supervisor",
            prompt,
            effort="medium",
            timeout=timeout_supervisor,
            log_name=f"supervisor_{role}",
        )
        lower = resp.strip().lower()
        if lower.startswith("redirect"):
            guidance = resp.split(":", 1)[1].strip() if ":" in resp else "Refocus on repo gaps."
            return False, guidance
        return True, ""

    def _run_static(extra_guidance: str | None = None) -> str:
        todo_hits = _scan_todos(
            repo_root,
            repo_map,
            focus_files=focus_files_set if focus_files else None,
        )
        prompt = (
            _workspace_override()
            + "You are the Static Analysis agent.\n"
            "Use ONLY the AST summary and TODO/FIXME list to find structure gaps.\n"
            f"{_repo_access_instruction()}\n"
            f"{_output_limit_note('Static')}\n"
            "Return bullets with file references.\n\n"
            f"Objective: {objective}\n"
            f"Problem Model:\n{problem_model_text}\n"
            f"AST summary:\n{ast_summary}\n"
            f"TODO/FIXME hits:\n{todo_hits or '- None found'}\n"
        )
        if extra_guidance:
            prompt += f"\nSupervisor guidance: {extra_guidance}\n"
        static_files = focus_files if focus_files else []
        static_hashes = _collect_file_hashes(static_files)
        static_input_hash = _hash_agent_input(
            "Static",
            static_hashes,
            {"objective": objective, "repo_hash": repo_hash},
        )
        static_cached = _cache_lookup(analysis_db, "Static", static_input_hash)
        output = _call_llm(
            "Static",
            prompt,
            effort="low",
            timeout=timeout_static,
            log_name="static",
            cached_output=static_cached,
            cache_meta={"input_hash": static_input_hash, "repo_hash": repo_hash},
        )
        if static_cached is None:
            _cache_store(
                analysis_db,
                agent="Static",
                input_hash=static_input_hash,
                repo_hash=repo_hash,
                file_hashes=static_hashes,
                output=output,
            )
        return output

    def _run_dynamic(extra_guidance: str | None = None) -> str:
        test_candidates = [
            repo_root / "tests",
            repo_root / "pytest.ini",
            repo_root / "pyproject.toml",
        ]
        tests_present = any(p.exists() for p in test_candidates)
        dynamic_files = focus_files if focus_files else []
        dynamic_hashes = _collect_file_hashes(dynamic_files)
        dynamic_input_hash = _hash_agent_input(
            "Dynamic",
            dynamic_hashes,
            {"objective": objective, "repo_hash": repo_hash, "tests_present": tests_present},
        )
        dynamic_cached = _cache_lookup(analysis_db, "Dynamic", dynamic_input_hash)
        dynamic_log = ""
        if dynamic_cached is None:
            dynamic_log = _run_dynamic_checks(repo_root, run_root)
        prompt = (
            _workspace_override()
            + "You are the Dynamic Verification agent.\n"
            "Use ONLY the runtime check log below (imports/tests).\n"
            "Do NOT inspect code or docs. Do NOT ask for permission.\n"
            "Return bullets with command outputs and implications.\n\n"
            f"{_output_limit_note('Dynamic')}\n"
            f"Objective: {objective}\n"
            f"Problem Model:\n{problem_model_text}\n"
            f"Runtime log:\n{dynamic_log or '- (cached)'}\n"
        )
        if extra_guidance:
            prompt += f"\nSupervisor guidance: {extra_guidance}\n"
        output = _call_llm(
            "Dynamic",
            prompt,
            effort="medium",
            timeout=timeout_dynamic,
            log_name="dynamic",
            cached_output=dynamic_cached,
            cache_meta={"input_hash": dynamic_input_hash, "repo_hash": repo_hash},
        )
        if dynamic_cached is None:
            _cache_store(
                analysis_db,
                agent="Dynamic",
                input_hash=dynamic_input_hash,
                repo_hash=repo_hash,
                file_hashes=dynamic_hashes,
                output=output,
            )
        return output

    def _run_research(gap_topics: list[str], extra_guidance: str | None = None) -> str:
        research_snippets: list[str] = []
        research_input_hash = _hash_agent_input(
            "Research",
            {},
            {"objective": objective, "repo_hash": repo_hash, "gap_topics": gap_topics[:6]},
        )
        research_cached = _cache_lookup(analysis_db, "Research", research_input_hash)
        if research_cached is None:
            try:
                from agent.autonomous.config import RunContext
                from agent.autonomous.tools.builtins import WebSearchArgs, web_search

                ctx = RunContext(
                    run_id="swarm_simple_research",
                    run_dir=run_root,
                    workspace_dir=run_root,
                    profile=None,
                    usage=None,
                )
                for topic in gap_topics[:4]:
                    query = f"best practices for {topic}"
                    search = web_search(ctx, WebSearchArgs(query=query, max_results=5))
                    results = (search.output or {}).get("results") or []
                    for result in results[:3]:
                        title = result.get("title") or "Untitled"
                        url = result.get("url") or ""
                        snippet = result.get("snippet") or ""
                        research_snippets.append(f"- {title} | {url} | {snippet}")
            except Exception as exc:
                research_snippets.append(f"- [ERROR] web_search failed: {exc}")

        prompt = (
            _workspace_override()
            + "You are the Research agent.\n"
            "Use ONLY web search to find best practices (no code analysis).\n"
            "Do NOT ask for permission.\n"
            "Return bullets with citations (raw URLs).\n\n"
            f"{_output_limit_note('Research')}\n"
            f"Objective: {objective}\n"
            f"Problem Model:\n{problem_model_text}\n"
            f"Gap topics: {gap_topics}\n"
            f"Research snippets:\n{chr(10).join(research_snippets) if research_snippets else '- None'}\n"
        )
        if extra_guidance:
            prompt += f"\nSupervisor guidance: {extra_guidance}\n"
        output = _call_llm(
            "Research",
            prompt,
            effort="medium",
            timeout=timeout_research,
            log_name="research",
            cached_output=research_cached,
            cache_meta={"input_hash": research_input_hash, "repo_hash": repo_hash},
            enable_search=True,
        )
        if research_cached is None:
            _cache_store(
                analysis_db,
                agent="Research",
                input_hash=research_input_hash,
                repo_hash=repo_hash,
                file_hashes={},
                output=output,
            )
        return output

    # Seed research topics from fingerprint so Research can run in parallel
    gap_topics_seed = _extract_gap_topics(
        "\n".join([fingerprint_text, "\n".join(claims), "\n".join(promises), "\n".join(checklist)]),
        limit=6,
    )

    # Run Static + Dynamic + Research in parallel
    outputs: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(_run_static): "Static",
            executor.submit(_run_dynamic): "Dynamic",
            executor.submit(_run_research, gap_topics_seed): "Research",
        }
        for future, role in list(futures.items()):
            try:
                outputs[role] = future.result()
            except Exception as exc:
                outputs[role] = f"[FAILED - {type(exc).__name__}]"

    # Supervisor checks & re-run if needed
    for role in ("Static", "Dynamic", "Research"):
        ok, guidance = _supervisor_check(role, outputs.get(role, ""))
        if not ok:
            if role == "Static":
                outputs[role] = _run_static(guidance)
            elif role == "Dynamic":
                outputs[role] = _run_dynamic(guidance)
            else:
                outputs[role] = _run_research(gap_topics_seed, guidance)

    gap_topics = []
    for source in (
        fingerprint_text,
        outputs.get("Static", ""),
        outputs.get("Dynamic", ""),
        outputs.get("Research", ""),
    ):
        gap_topics.extend(_extract_gap_topics(source, limit=6))
    # de-dupe
    deduped = []
    for topic in gap_topics:
        if topic.lower() not in {t.lower() for t in deduped}:
            deduped.append(topic)
    gap_topics = deduped[:6]

    # Critic agent
    def _build_critic_prompt() -> str:
        return (
            _workspace_override()
            + "You are the Critic agent.\n"
            "Verify each finding: is it real, important, and supported?\n"
            "Score confidence per agent (static/dynamic/research) from 0-1 and overall avg.\n"
            "Measure disagreement by the spread of scores.\n"
            "If average confidence <0.70, include REANALYZE: Agent -> guidance.\n"
            "Return sections:\n"
            "VERIFY:\n- Gap: ... | static=0.xx | dynamic=0.xx | research=0.xx | avg=0.xx | notes: ...\n"
            "REFLECT:\nREANALYZE: <Agent> -> <guidance>\n"
            "AVERAGE_CONFIDENCE: 0.xx\n"
            "Do NOT ask for permission.\n"
            f"{_output_limit_note('Critic')}\n"
            f"Objective: {objective}\n"
            f"Problem Model:\n{problem_model_text}\n"
            f"Fingerprint:\n{fingerprint_text}\n"
            f"Static findings:\n{outputs.get('Static','')}\n"
            f"Dynamic findings:\n{outputs.get('Dynamic','')}\n"
            f"Research findings:\n{outputs.get('Research','')}\n"
        )

    def _log_uncertain(uncertain: list[dict]) -> None:
        if not uncertain:
            return
        print("\n[SWARM SIMPLE] Uncertain gaps (high disagreement):")
        for gap in uncertain:
            variance = gap.get("variance")
            label = gap.get("gap") or "(unknown gap)"
            if isinstance(variance, (int, float)):
                print(f"- {label} | variance={variance:.2f}")
            else:
                print(f"- {label} | variance=unknown")

    critic_prompt = _build_critic_prompt()
    critic_text = _call_llm("Critic", critic_prompt, effort="high", timeout=timeout_critic, log_name="critic")
    gap_scores = _parse_confidence_lines(critic_text)
    global_avg, agent_avgs, uncertain = _confidence_stats(gap_scores)
    _log_uncertain(uncertain)

    reanalysis = _parse_reanalysis(critic_text)
    if global_avg is not None and global_avg < 0.7 and not reanalysis:
        weakest = min(agent_avgs, key=agent_avgs.get) if agent_avgs else "Static"
        reanalysis = {
            weakest: "Overall confidence <0.70; add evidence and file references for weak gaps."
        }
        print(f"[Critic] Low average confidence; forcing reanalysis of {weakest}.")
    if reanalysis:
        for agent, guidance in reanalysis.items():
            if agent == "Static":
                outputs["Static"] = _run_static(guidance)
            elif agent == "Dynamic":
                outputs["Dynamic"] = _run_dynamic(guidance)
            elif agent == "Research":
                outputs["Research"] = _run_research(gap_topics, guidance)
        # Re-run critic once after reanalysis
        critic_prompt = _build_critic_prompt()
        critic_text = _call_llm("Critic", critic_prompt, effort="high", timeout=timeout_critic, log_name="critic_retry")
        gap_scores = _parse_confidence_lines(critic_text)
        global_avg, agent_avgs, uncertain = _confidence_stats(gap_scores)
        _log_uncertain(uncertain)

    # Synthesis agent
    synthesis_prompt = (
        _workspace_override()
        + "You are the Synthesis agent.\n"
        "Combine findings and prioritize by impact × confidence.\n"
        "Return:\n"
        "PRIORITIZED GAPS (with citations)\n"
        "RECOMMENDATIONS (actionable, cited)\n"
        "QUESTIONS (clarifying)\n"
        "Do NOT ask for permission.\n"
        f"{_output_limit_note('Synthesis')}\n"
        f"Objective: {objective}\n"
        f"Problem Model:\n{problem_model_text}\n"
        f"Fingerprint:\n{fingerprint_text}\n"
        f"Static findings:\n{outputs.get('Static','')}\n"
        f"Dynamic findings:\n{outputs.get('Dynamic','')}\n"
        f"Research findings:\n{outputs.get('Research','')}\n"
        f"Critic review:\n{critic_text}\n"
    )
    synthesis_text = _call_llm("Synthesis", synthesis_prompt, effort="medium", timeout=timeout_synthesis, log_name="synthesis")

    print("\n[SWARM SIMPLE] Results:")
    for role in ["Static", "Dynamic", "Research"]:
        out = outputs.get(role, "[FAILED - no result]")
        if out.startswith("[FAILED"):
            print(f"\n[{role}] {out}")
        elif _is_incomplete_observation(out):
            print(f"\n[{role}] [INCOMPLETE] Observation-only response")
        else:
            print(f"\n[{role}]\n{out}")
    print(f"\n[Critic]\n{critic_text}")
    print(f"\n[Synthesis]\n{synthesis_text}")
    if analysis_db is not None:
        try:
            analysis_db.close()
        except Exception:
            pass


def aggregate_swarm_results(
    futures: List,
    timeout: int = 30,
) -> SwarmResult:
    """Aggregate results from all workers, handling failures.

    This function collects results from all workers, handling timeouts
    and exceptions gracefully. It always returns a SwarmResult with
    whatever results were successfully collected.

    Args:
        futures: List of futures from worker tasks
        timeout: Timeout per worker in seconds

    Returns:
        SwarmResult with results and failures
    """
    results = []
    failures = []

    for future in as_completed(futures, timeout=timeout):
        try:
            result = future.result(timeout=timeout)
            results.append(result)
            logger.info("Worker completed: %s", getattr(result, "task_id", "unknown"))

        except TimeoutError as exc:
            logger.error("Worker timed out: %s", exc)
            failures.append({
                "type": "timeout",
                "error": str(exc),
                "task_id": getattr(future, "task_id", "unknown"),
            })

        except AgentException as exc:
            logger.error("Agent error in worker: %s", exc)
            failures.append({
                "type": "agent_error",
                "error": str(exc),
                "error_type": type(exc).__name__,
                "task_id": getattr(future, "task_id", "unknown"),
            })

        except Exception as exc:
            logger.error("Worker failed: %s", exc, exc_info=True)
            failures.append({
                "type": "exception",
                "error": str(exc),
                "error_type": type(exc).__name__,
                "task_id": getattr(future, "task_id", "unknown"),
            })

    # Determine overall status
    if not failures:
        status = "success"
    elif results:
        status = "partial_failure"
    else:
        status = "failure"

    # Create summary
    summary = f"Completed {len(results)}/{len(futures)} tasks"
    if failures:
        summary += f" ({len(failures)} failures)"

    return SwarmResult(
        status=status,
        results=results,
        failures=failures,
        summary=summary,
    )


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except Exception:
        return


def _bool_env(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "y", "on"}


def _int_env(name: str, default: int) -> int:
    val = os.getenv(name)
    if val is None or not str(val).strip():
        return default
    try:
        return int(str(val).strip())
    except Exception:
        return default


def _split_paths(raw: str) -> list[Path]:
    parts = [p.strip() for p in raw.split(";") if p.strip()]
    return [Path(p) for p in parts]


def _choose_planner_mode(task: str) -> str:
    text = (task or "").strip().lower()
    if not text:
        return "react"
    words = [w for w in re.split(r"\s+", text) if w]
    word_count = len(words)
    conjunctions = (" and ", " then ", " after ", " before ", " also ", " plus ")
    plan_keywords = (
        "plan",
        "steps",
        "roadmap",
        "multi-step",
        "implement",
        "build",
        "create",
        "setup",
        "configure",
        "migrate",
        "refactor",
        "research",
        "compare",
        "analyze",
        "summarize",
    )
    if word_count >= 12:
        return "plan_first"
    if any(k in text for k in conjunctions):
        return "plan_first"
    if text.count(",") >= 2 or ":" in text or ";" in text:
        return "plan_first"
    if any(k in text for k in plan_keywords):
        return "plan_first"
    return "react"


def _default_allowed_roots(repo_root: Path) -> Tuple[Path, ...]:
    return (repo_root,)


def _build_agent_cfg(
    repo_root: Path,
    *,
    unsafe_mode: bool,
    profile_name: str | None,
    allow_interactive_tools: bool = True,
) -> AgentConfig:
    profile = resolve_profile(profile_name, env_keys=("SWARM_PROFILE", "AUTO_PROFILE", "AGENT_PROFILE"))
    fs_anywhere = _bool_env("SWARM_FS_ANYWHERE", _bool_env("AUTO_FS_ANYWHERE", False))
    raw_roots = os.getenv("SWARM_FS_ALLOWED_ROOTS") or os.getenv("AUTO_FS_ALLOWED_ROOTS") or ""
    allowed_roots = _split_paths(raw_roots) if raw_roots.strip() else list(_default_allowed_roots(repo_root))
    return AgentConfig(
        unsafe_mode=bool(unsafe_mode),
        enable_web_gui=_bool_env("SWARM_ENABLE_WEB_GUI", _bool_env("AUTO_ENABLE_WEB_GUI", False)),
        enable_desktop=_bool_env("SWARM_ENABLE_DESKTOP", _bool_env("AUTO_ENABLE_DESKTOP", False)),
        pre_mortem_enabled=_bool_env("SWARM_PRE_MORTEM", _bool_env("AUTO_PRE_MORTEM", False)),
        allow_user_info_storage=_bool_env(
            "SWARM_ALLOW_USER_INFO_STORAGE", _bool_env("AUTO_ALLOW_USER_INFO_STORAGE", False)
        ),
        allow_human_ask=bool(profile.allow_interactive),
        allow_interactive_tools=bool(allow_interactive_tools),
        allow_fs_anywhere=fs_anywhere,
        fs_allowed_roots=tuple(allowed_roots),
        profile=profile,
    )


def _build_runner_cfg(profile_name: str | None) -> RunnerConfig:
    profile = resolve_profile(profile_name, env_keys=("SWARM_PROFILE", "AUTO_PROFILE", "AGENT_PROFILE"))
    max_steps = _int_env("SWARM_MAX_STEPS", _int_env("AUTO_MAX_STEPS", 30))
    timeout_seconds = _int_env("SWARM_TIMEOUT_SECONDS", _int_env("AUTO_TIMEOUT_SECONDS", 600))
    heartbeat = _int_env("SWARM_LLM_HEARTBEAT_SECONDS", profile.heartbeat_s)
    plan_timeout = _int_env("SWARM_LLM_PLAN_TIMEOUT_SECONDS", profile.plan_timeout_s)
    retry_timeout = _int_env("SWARM_LLM_PLAN_RETRY_TIMEOUT_SECONDS", profile.plan_retry_timeout_s)
    return RunnerConfig(
        max_steps=max_steps,
        timeout_seconds=timeout_seconds,
        llm_heartbeat_seconds=heartbeat,
        llm_plan_timeout_seconds=plan_timeout,
        llm_plan_retry_timeout_seconds=retry_timeout,
    )


def _planner_mode_for(task: str) -> str:
    mode = (os.getenv("SWARM_PLANNER_MODE") or "auto").strip().lower()
    if mode == "auto":
        return _choose_planner_mode(task)
    return mode if mode in {"react", "plan_first"} else "react"


def _swarm_run_dir() -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"
    return repo_root / "runs" / "swarm" / run_id


@dataclass
class Subtask:
    id: str
    goal: str
    depends_on: List[str]
    notes: str


def _decompose(
    llm: CodexCliClient,
    objective: str,
    *,
    max_items: int,
    clarify: ClarifyResult,
    preflight: PreflightResult,
) -> List[Subtask]:
    prompt = (
        "You are a swarm coordinator. Decompose the objective into 2-4 parallelizable subtasks.\n"
        "Only add dependencies when truly required. Use short IDs like A, B, C.\n"
        "Use the preflight repo_map and root listing; do NOT scan the entire repo.\n"
        "If the objective is a repo review, review only selected files from repo_map.\n"
        "If task_type is find_filepath, follow this structure:\n"
        "  A: Use repo_map + search_terms to list candidate paths.\n"
        "  B: Validate by opening only those candidate files/paths.\n"
        "  C: Return best match + rationale + next candidates.\n"
        f"Normalized objective: {objective}\n"
        f"Task type: {clarify.task_type}\n"
        f"Search terms: {clarify.search_terms}\n"
        f"Glob patterns: {clarify.glob_patterns}\n"
        f"Candidate roots: {clarify.candidate_roots}\n"
        f"Expected output: {clarify.expected_output}\n"
        f"Preflight repo_map: {preflight.repo_map_path}\n"
        f"Preflight root listing: {preflight.root_listing_path}\n"
        "Return JSON only."
    )
    data = llm.reason_json(prompt, schema_path=llm_schemas.TASK_DECOMPOSITION)
    raw = data.get("subtasks") if isinstance(data, dict) else None
    if not isinstance(raw, list):
        return []
    items: List[Subtask] = []
    for idx, entry in enumerate(raw[:max_items], 1):
        if not isinstance(entry, dict):
            continue
        sid = str(entry.get("id") or f"S{idx}").strip()
        goal = str(entry.get("goal") or "").strip()
        if not goal:
            continue
        depends_on = entry.get("depends_on")
        if not isinstance(depends_on, list):
            depends_on = []
        notes = str(entry.get("notes") or "").strip()
        items.append(Subtask(id=sid, goal=goal, depends_on=[str(d) for d in depends_on], notes=notes))
    return items


def _ensure_repo_scan_subtask(subtasks: List[Subtask], *, objective: str, max_items: int) -> None:
    if not is_repo_review_task(objective):
        return
    repo_goal = (
        "Stage A: use repo_index.json and repo_map.json in this run directory. "
        "Only read files listed in repo_map.json (no broad globbing). "
        "Write A_findings.json summarizing repo structure, key files, and risks."
    )
    a_task = next((s for s in subtasks if s.id.strip().upper() == "A"), None)
    if a_task is None:
        if len(subtasks) < max_items:
            subtasks.insert(0, Subtask(id="A", goal=repo_goal, depends_on=[], notes=""))
            return
        a_task = subtasks[0]
        old_id = a_task.id
        a_task.id = "A"
        for s in subtasks[1:]:
            s.depends_on = ["A" if d == old_id else d for d in s.depends_on]
    if repo_goal not in a_task.goal:
        a_task.goal = f"{repo_goal}\n\n{a_task.goal}".strip()


def _ask_blocking_questions(questions: List[Dict[str, Any]]) -> Dict[str, Any]:
    prompts: List[str] = []
    for q in questions:
        question = str(q.get("question") or "").strip()
        if not question:
            continue
        prompts.append(question)
    return {
        "error": "interaction_required",
        "questions": prompts,
        "context": "swarm_initialization",
    }


def _format_answers(answers: Dict[str, str]) -> str:
    lines = []
    for key, val in answers.items():
        if not val:
            continue
        lines.append(f"{key}: {val}")
    return "\n".join(lines)


def _annotate_subtasks(
    subtasks: List[Subtask],
    *,
    clarify: ClarifyResult,
    preflight: PreflightResult,
) -> List[Subtask]:
    prefix_lines = [
        f"Preflight repo_map: {preflight.repo_map_path}",
        f"Preflight root listing: {preflight.root_listing_path}",
    ]
    if clarify.search_terms:
        prefix_lines.append(f"Search terms: {clarify.search_terms}")
    if clarify.glob_patterns:
        prefix_lines.append(f"Glob patterns: {clarify.glob_patterns}")
    if clarify.candidate_roots:
        prefix_lines.append(f"Candidate roots: {clarify.candidate_roots}")
    prefix = "\n".join(prefix_lines).strip()
    if not prefix:
        return subtasks
    updated = []
    for s in subtasks:
        updated.append(Subtask(id=s.id, goal=f"{prefix}\n\n{s.goal}".strip(), depends_on=s.depends_on, notes=s.notes))
    return updated


def _select_isolation_mode(profile_name: str, explicit: str | None) -> str:
    raw = (explicit or os.getenv("SWARM_ISOLATION") or "").strip().lower()
    if raw in {"none", "sandbox", "worktree"}:
        return raw
    if profile_name in {"deep", "audit"}:
        return "sandbox"
    return "none"


def _workspace_note(goal: str, workspace: Path) -> str:
    note = (
        "Use the isolated workspace at:\n"
        f"{workspace}\n"
        "All file operations should stay inside this workspace."
    )
    return f"{note}\n\n{goal}".strip()


def _build_isolated_agent_cfg(agent_cfg: AgentConfig, *, repo_root: Path, workspace: Path) -> AgentConfig:
    roots = [r for r in agent_cfg.fs_allowed_roots if r != repo_root]
    if workspace not in roots:
        roots.append(workspace)
    return replace(agent_cfg, fs_allowed_roots=tuple(roots))


def _expected_artifacts_for(subtask: Subtask) -> List[str]:
    expected = ["result.json", "trace.jsonl"]
    goal = subtask.goal.lower()
    if "repo_map" in goal or "repo_index" in goal:
        expected.extend(["repo_index.json", "repo_map.json"])
    if "a_findings" in goal or subtask.id.strip().upper() == "A":
        expected.append("A_findings.json")
    return list(dict.fromkeys(expected))


def _should_run_tests(objective: str, subtasks: Iterable[Subtask]) -> bool:
    text = (objective or "").lower()
    keywords = (
        "implement",
        "refactor",
        "fix",
        "change",
        "modify",
        "update",
        "code",
        "add",
        "remove",
    )
    if any(k in text for k in keywords):
        return True
    for sub in subtasks:
        goal = sub.goal.lower()
        if any(k in goal for k in keywords):
            return True
    return False


def _build_reduced_goal(
    subtask: Subtask,
    *,
    failed_deps: List[str],
    results_by_id: Dict[str, Dict[str, Any]],
    run_dirs_by_id: Dict[str, Path],
    subtasks_by_id: Dict[str, Subtask],
) -> str:
    lines = [
        "Reduced synthesis mode: one or more dependencies failed.",
        "Summarize what failed and why based on available result.json/trace.jsonl.",
        "List missing artifacts per dependency.",
        "Propose next-run objectives and minimal inputs needed.",
        "",
        f"Failed dependencies: {', '.join(failed_deps)}",
        "Failure details:",
    ]
    for dep in failed_deps:
        result = results_by_id.get(dep, {})
        reason = ""
        if isinstance(result.get("error"), dict):
            err = result.get("error") or {}
            reason = err.get("message") or err.get("type") or ""
        reason = reason or str(result.get("stop_reason") or result.get("reason") or "unknown")
        lines.append(f"- {dep}: {reason}")
    lines.append("")
    lines.append("Missing artifacts:")
    for dep in failed_deps:
        dep_task = subtasks_by_id.get(dep, Subtask(id=dep, goal="", depends_on=[], notes=""))
        dep_dir = run_dirs_by_id.get(dep)
        expected = _expected_artifacts_for(dep_task)
        missing = []
        if dep_dir is not None:
            for name in expected:
                if not (dep_dir / name).exists():
                    missing.append(name)
        if missing:
            lines.append(f"- {dep}: {missing}")
    lines.append("")
    lines.append("Original goal (for context only):")
    lines.append(subtask.goal)
    return "\n".join(lines)


def _trace_tail(trace_path: str, *, max_lines: int = 200) -> List[dict]:
    try:
        path = Path(trace_path)
        if not path.is_file():
            return []
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        tail = lines[-max_lines:]
        events: List[dict] = []
        for line in tail:
            line = line.strip()
            if not line:
                continue
            try:
                evt = json.loads(line)
            except Exception:
                continue
            if evt.get("type") in {"finish", "stop", "error_report", "tool_retry", "observation"}:
                events.append(evt)
        return events[-40:]
    except Exception:
        return []


def _read_result(run_dir: Path) -> Dict[str, Any]:
    try:
        path = run_dir / "result.json"
        if not path.is_file():
            return {}
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return {}


def _write_result(run_dir: Path, payload: Dict[str, Any]) -> None:
    try:
        run_dir.mkdir(parents=True, exist_ok=True)
        path = run_dir / "result.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def _run_subagent(
    subtask: Subtask,
    *,
    repo_root: Path,
    run_dir: Path,
    agent_cfg: AgentConfig,
    runner_cfg: RunnerConfig,
    unsafe_mode: bool,
    workdir: Optional[Path] = None,
) -> tuple[Subtask, str, str, Path]:
    # Threaded swarm runs must never mutate process-global state (e.g., os.chdir).
    _debug_agent_banner(f"Swarm {subtask.id}")
    planner_mode = _planner_mode_for(subtask.goal)
    planner_cfg = PlannerConfig(
        mode=planner_mode,  # type: ignore[arg-type]
        num_candidates=_int_env("SWARM_NUM_CANDIDATES", _int_env("AUTO_NUM_CANDIDATES", 1)),
        max_plan_steps=_int_env("SWARM_MAX_PLAN_STEPS", _int_env("AUTO_MAX_PLAN_STEPS", 6)),
    )
    try:
        llm = CodexCliClient.from_env(workdir=workdir or repo_root, log_dir=run_dir)
    except (CodexCliNotFoundError, CodexCliAuthError) as exc:
        return subtask, "failed", f"llm_error: {exc}", ""

    runner = AgentRunner(
        cfg=runner_cfg,
        agent_cfg=agent_cfg,
        planner_cfg=planner_cfg,
        llm=llm,
        run_dir=run_dir,
        mode_name="swarm_subagent",
        agent_id=subtask.id,
    )
    result = runner.run(subtask.goal)
    status = "success" if result.success else "failed"
    return subtask, status, result.stop_reason or "", run_dir


def mode_swarm(
    objective: str,
    *,
    unsafe_mode: bool = False,
    profile: str | None = None,
    isolation: str | None = None,
    cleanup_worktrees: bool | None = None,
) -> None:
    _load_dotenv()
    try:
        llm = CodexCliClient.from_env()
    except CodexCliNotFoundError as exc:
        print(f"[ERROR] {exc}")
        return
    except CodexCliAuthError as exc:
        print(f"[ERROR] {exc}")
        return

    repo_root = Path(__file__).resolve().parents[2]
    run_root = _swarm_run_dir()
    run_root.mkdir(parents=True, exist_ok=True)

    max_subtasks = max(1, _int_env("SWARM_MAX_SUBTASKS", 3))
    profile_cfg = resolve_profile(profile, env_keys=("SWARM_PROFILE", "AUTO_PROFILE", "AGENT_PROFILE"))
    workers = max(1, _int_env("SWARM_MAX_WORKERS", profile_cfg.workers))
    isolation_mode = _select_isolation_mode(profile_cfg.name, isolation)
    cleanup_worktrees = (
        bool(cleanup_worktrees)
        if cleanup_worktrees is not None
        else _bool_env("SWARM_CLEANUP_WORKTREES", False)
    )

    llm = llm.with_context(workdir=repo_root, log_dir=run_root)

    preflight_dir = run_root / "preflight"
    preflight = run_preflight(
        repo_root=repo_root,
        objective=objective,
        run_dir=preflight_dir,
        max_results=min(profile_cfg.max_glob_results, 200),
        max_map_files=min(profile_cfg.max_files_to_read, 20),
        max_total_bytes=min(profile_cfg.max_total_bytes_to_read, 200_000),
    )
    clarify = run_clarifier(
        llm,
        objective=objective,
        root_listing=preflight.root_listing,
        repo_map=preflight.repo_map,
        run_dir=preflight_dir,
        workdir=repo_root,
        timeout_seconds=profile_cfg.plan_timeout_s,
    )
    if not clarify.ready_to_run and clarify.blocking_questions:
        print("\n[SWARM] Clarification needed before starting workers:")
        answers = _ask_blocking_questions(clarify.blocking_questions)
        if isinstance(answers, dict) and answers.get("error") == "interaction_required":
            _write_result(
                run_root,
                {
                    "ok": False,
                    "mode": "swarm",
                    "run_id": run_root.name,
                    "error": {
                        "type": "interaction_required",
                        "message": "interaction_required",
                        "data": answers,
                    },
                },
            )
            print("[SWARM] interaction_required:", answers.get("questions"))
            return
        if answers:
            augmented = objective + "\n\nUser answers:\n" + _format_answers(answers)
            clarify = run_clarifier(
                llm,
                objective=augmented,
                root_listing=preflight.root_listing,
                repo_map=preflight.repo_map,
                run_dir=preflight_dir,
                workdir=repo_root,
                timeout_seconds=profile_cfg.plan_timeout_s,
            )
    normalized_objective = clarify.normalized_objective or objective

    subtasks = _decompose(
        llm,
        normalized_objective,
        max_items=max_subtasks,
        clarify=clarify,
        preflight=preflight,
    )
    if not subtasks:
        print("[SWARM] Could not decompose; running as a single Auto task.")
        from agent.modes.autonomous import mode_autonomous

        mode_autonomous(normalized_objective, unsafe_mode=unsafe_mode)
        return
    subtasks = _annotate_subtasks(subtasks, clarify=clarify, preflight=preflight)
    _ensure_repo_scan_subtask(subtasks, objective=normalized_objective, max_items=max_subtasks)

    print(f"\n[SWARM] Objective: {objective}")
    print(f"[SWARM] Subtasks: {len(subtasks)} | Workers: {workers}")
    for s in subtasks:
        deps = f" (deps: {', '.join(s.depends_on)})" if s.depends_on else ""
        print(f"  - {s.id}: {s.goal}{deps}")

    agent_cfg = _build_agent_cfg(
        repo_root,
        unsafe_mode=unsafe_mode,
        profile_name=profile,
        allow_interactive_tools=False,
    )
    runner_cfg = _build_runner_cfg(profile)
    write_run_manifest(
        run_root,
        run_id=run_root.name,
        profile=profile_cfg,
        runner_cfg=runner_cfg,
        workers=workers,
        mode="swarm",
    )
    if not agent_cfg.enable_web_gui and not agent_cfg.enable_desktop:
        print("[SWARM] MCP-based tools disabled (web_gui/desktop). Using local file/Python/web_fetch tools only.")

    remaining: Dict[str, Subtask] = {s.id: s for s in subtasks}
    completed: set[str] = set()
    results: List[tuple[Subtask, str, str, Path]] = []
    results_by_id: Dict[str, Dict[str, Any]] = {}
    run_dirs_by_id: Dict[str, Path] = {}
    status_by_id: Dict[str, str] = {}
    subtasks_by_id: Dict[str, Subtask] = {s.id: s for s in subtasks}
    worktrees_by_id: Dict[str, WorktreeInfo] = {}
    orchestrator = TaskOrchestrator()

    while remaining:
        ready = [s for s in remaining.values() if all(d in completed for d in s.depends_on)]
        if not ready:
            ready = list(remaining.values())

        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_map: Dict[Any, tuple[Subtask, Path]] = {}
            for s in ready:
                _reduce, dep_failures = orchestrator.should_reduce(s.depends_on, status_by_id)
                subtask = s
                if dep_failures:
                    reduced_goal = _build_reduced_goal(
                        s,
                        failed_deps=dep_failures,
                        results_by_id=results_by_id,
                        run_dirs_by_id=run_dirs_by_id,
                        subtasks_by_id=subtasks_by_id,
                    )
                    subtask = Subtask(id=s.id, goal=reduced_goal, depends_on=s.depends_on, notes=s.notes)
                sub_dir = run_root / f"{s.id}_{uuid4().hex[:6]}"
                sub_dir.mkdir(parents=True, exist_ok=True)
                workdir = repo_root
                sub_agent_cfg = agent_cfg
                if isolation_mode != "none":
                    workspace_dir = sub_dir / "workspace"
                    workspace_dir.mkdir(parents=True, exist_ok=True)
                    if isolation_mode == "sandbox":
                        copy_repo_to_workspace(repo_root, workspace_dir)
                    elif isolation_mode == "worktree":
                        branch = sanitize_branch_name(f"swarm/{run_root.name}/{s.id}-{uuid4().hex[:6]}")
                        info = create_worktree(repo_root, workspace_dir, branch)
                        worktrees_by_id[s.id] = info
                    workdir = workspace_dir
                    sub_agent_cfg = _build_isolated_agent_cfg(agent_cfg, repo_root=repo_root, workspace=workspace_dir)
                    subtask = Subtask(
                        id=subtask.id,
                        goal=_workspace_note(subtask.goal, workspace_dir),
                        depends_on=subtask.depends_on,
                        notes=subtask.notes,
                    )
                future = executor.submit(
                    _run_subagent,
                    subtask,
                    repo_root=repo_root,
                    run_dir=sub_dir,
                    agent_cfg=sub_agent_cfg,
                    runner_cfg=runner_cfg,
                    unsafe_mode=unsafe_mode,
                    workdir=workdir,
                )
                future_map[future] = (s, sub_dir)

            for future in as_completed(future_map):
                subtask, fallback_dir = future_map[future]
                try:
                    subtask, status, stop_reason, sub_run_dir = future.result()
                except Exception as exc:
                    sub_run_dir = fallback_dir
                    _write_result(
                        sub_run_dir,
                        {
                            "ok": False,
                            "mode": "swarm_subagent",
                            "agent_id": subtask.id,
                            "run_id": subtask.id,
                            "error": {
                                "type": type(exc).__name__,
                                "message": str(exc),
                                "traceback": traceback.format_exc(),
                            },
                        },
                    )
                    status = "failed"
                    stop_reason = f"exception:{type(exc).__name__}"
                results.append((subtask, status, stop_reason, sub_run_dir))
                run_dirs_by_id[subtask.id] = sub_run_dir
                results_by_id[subtask.id] = _read_result(sub_run_dir)
                status_by_id[subtask.id] = "success" if status == "success" else "failed"
                completed.add(subtask.id)
                if subtask.id in remaining:
                    del remaining[subtask.id]
                if cleanup_worktrees and subtask.id in worktrees_by_id:
                    remove_worktree(repo_root, worktrees_by_id[subtask.id])

    print("\n[SWARM] Results:")
    for subtask, status, stop_reason, sub_run_dir in results:
        # result.json is the canonical outcome; terminal output is a convenience.
        result_data = _read_result(sub_run_dir)
        ok = result_data.get("ok")
        if isinstance(ok, bool):
            status = "success" if ok else "failed"
        if isinstance(result_data.get("error"), dict):
            err = result_data["error"]
            stop_reason = err.get("message") or err.get("type") or stop_reason
            data = err.get("data") if isinstance(err, dict) else None
            if isinstance(data, dict) and data.get("questions"):
                stop_reason = f"{stop_reason} | questions: {data.get('questions')}"
        line = f"- {subtask.id}: {status}"
        if stop_reason:
            line += f" | {stop_reason}"
        print(line)
        trace_path = sub_run_dir / "trace.jsonl"
        if trace_path.is_file():
            print(f"  trace: {trace_path}")

    if _bool_env("SWARM_SUMMARIZE", True):
        tails = []
        for subtask, status, stop_reason, sub_run_dir in results:
            result_data = _read_result(sub_run_dir)
            ok = result_data.get("ok")
            if isinstance(ok, bool):
                status = "success" if ok else "failed"
            if isinstance(result_data.get("error"), dict):
                err = result_data["error"]
                stop_reason = err.get("message") or err.get("type") or stop_reason
                data = err.get("data") if isinstance(err, dict) else None
                if isinstance(data, dict) and data.get("questions"):
                    stop_reason = f"{stop_reason} | questions: {data.get('questions')}"
            trace_path = sub_run_dir / "trace.jsonl"
            if trace_path.is_file():
                tails.append(
                    {
                        "id": subtask.id,
                        "goal": subtask.goal,
                        "status": status,
                        "stop_reason": stop_reason,
                        "trace_tail": _trace_tail(str(trace_path)),
                    }
                )
        prompt = (
            "Summarize the swarm results and propose next steps.\n"
            "Be concise and action-oriented.\n\n"
            f"Objective: {objective}\n"
            f"Subtask results: {json.dumps(tails, ensure_ascii=False)}\n"
        )
        data = llm.reason_json(prompt, schema_path=llm_schemas.CHAT_RESPONSE)
        if isinstance(data, dict):
            summary = (data.get("response") or "").strip()
            if summary:
                print("\n[SWARM] Summary:")
                print(summary)

    # QA validation
    qa_results: Dict[str, QaResult] = {}
    for subtask, _status, _stop_reason, sub_run_dir in results:
        expected = _expected_artifacts_for(subtask)
        qa_results[subtask.id] = validate_artifacts(sub_run_dir, expected)

    test_result: Optional[Dict[str, Any]] = None
    if _bool_env("SWARM_QA_RUN_TESTS", False) and _should_run_tests(objective, subtasks):
        cmd = os.getenv("SWARM_QA_COMMAND") or "python -m pytest -q"
        proc = subprocess.run(cmd, shell=True, cwd=str(repo_root), capture_output=True, text=True)
        stdout_tail = (proc.stdout or "").splitlines()[-10:]
        stderr_tail = (proc.stderr or "").splitlines()[-10:]
        message = " ".join(stdout_tail[-2:] + stderr_tail[-2:]).strip()
        test_result = {
            "ok": proc.returncode == 0,
            "command": cmd,
            "returncode": proc.returncode,
            "message": message or f"exit {proc.returncode}",
        }

    print("\n[SWARM] QA Summary:")
    for line in format_qa_summary(qa_results, test_result):
        print(line)

    print(f"[SWARM] Run folder: {run_root}")


__all__ = ["mode_swarm", "mode_swarm_simple"]


def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(prog="python -m agent.modes.swarm")
    p.add_argument("--objective", required=True, help="Objective for the swarm run.")
    p.add_argument("--profile", choices=["fast", "deep", "audit"], default=None)
    p.add_argument("--isolation", choices=["none", "sandbox", "worktree"], default=None)
    p.add_argument("--cleanup-worktrees", action="store_true")
    p.add_argument("--unsafe-mode", action="store_true")
    args = p.parse_args(argv)

    mode_swarm(
        args.objective,
        unsafe_mode=bool(args.unsafe_mode),
        profile=args.profile,
        isolation=args.isolation,
        cleanup_worktrees=bool(args.cleanup_worktrees),
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - convenience entrypoint
    raise SystemExit(main())
