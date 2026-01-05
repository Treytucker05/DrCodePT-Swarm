from __future__ import annotations

import asyncio
import html as html_lib
import logging
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import shlex
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4
from urllib.parse import parse_qs, unquote, urlparse

import requests
from pydantic import BaseModel, Field

from ..config import AgentConfig, RunContext
from agent.config.profile import ProfileConfig, RunUsage
from ..memory.sqlite_store import MemoryKind, SqliteMemoryStore
from ..models import ToolResult
from ..retry_utils import WEB_RETRY_CONFIG, retry_with_backoff
from .registry import ToolRegistry, ToolSpec, register_calendar_tasks_tools

logger = logging.getLogger(__name__)

# Lightweight in-memory sessions for GUI tools (keyed by run_id).
_WEB_SESSIONS: Dict[str, Dict[str, Any]] = {}
_DESKTOP_SOM_STATE: Dict[str, Dict[str, Any]] = {}

_SAFE_SHELL_COMMANDS = {"rg", "git", "python", "py", "pytest"}
_BLOCKED_SHELL_TOKENS = {"rm", "del", "erase", "format", "mkfs", "shutdown", "reboot"}
_BLOCKED_SHELL_CHARS = {"&&", "||", ";", "|", ">", "<"}


def _label_id(idx: int) -> str:
    # A1..Z9, then AA1.. if needed.
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if idx < 26 * 9:
        row = idx // 9
        col = (idx % 9) + 1
        return f"{letters[row]}{col}"
    # Fallback: L{idx}
    return f"L{idx}"


def _is_within(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except Exception:
        return False


def _fs_allowed(path: Path, cfg: AgentConfig, ctx: RunContext) -> bool:
    if cfg.allow_fs_anywhere:
        return True
    allowed: List[Path] = []
    allowed.extend(cfg.fs_allowed_roots or [])
    if ctx.workspace_dir:
        allowed.append(ctx.workspace_dir)
    if ctx.run_dir:
        allowed.append(ctx.run_dir)
    for root in allowed:
        try:
            if _is_within(path, root):
                return True
        except Exception:
            continue
    return False


def _get_profile(ctx: RunContext) -> Optional[ProfileConfig]:
    return getattr(ctx, "profile", None)


def _get_usage(ctx: RunContext) -> Optional[RunUsage]:
    return getattr(ctx, "usage", None)


def _cap_results(value: int, cap: Optional[int]) -> int:
    if cap is None:
        return value
    return min(value, cap)


def _command_root(command: str) -> str:
    try:
        parts = shlex.split(command, posix=False)
    except Exception:
        parts = command.strip().split()
    if not parts:
        return ""
    token = parts[0]
    name = Path(token).name.lower()
    for ext in (".exe", ".cmd", ".bat"):
        if name.endswith(ext):
            name = name[: -len(ext)]
    return name


def _shell_allowed(command: str, *, unsafe_mode: bool) -> tuple[bool, str]:
    if unsafe_mode:
        return True, ""
    if not command or not command.strip():
        return False, "empty command"
    lowered = command.lower()
    if any(ch in lowered for ch in _BLOCKED_SHELL_CHARS):
        return False, "chaining/pipes not allowed"
    if "http://" in lowered or "https://" in lowered:
        return False, "commands containing URLs are blocked by default"
    root = _command_root(command)
    if root in _BLOCKED_SHELL_TOKENS:
        return False, f"blocked command: {root}"
    if root not in _SAFE_SHELL_COMMANDS:
        return False, f"command not allowlisted: {root or 'unknown'}"
    return True, ""


class WebFetchArgs(BaseModel):
    url: str
    timeout_seconds: int = 15
    max_bytes: int = 1_000_000
    headers: Dict[str, str] = Field(default_factory=dict)
    strip_html: bool = False


def web_fetch(ctx: RunContext, args: WebFetchArgs) -> ToolResult:
    profile = _get_profile(ctx)
    usage = _get_usage(ctx)
    if profile and usage and usage.web_sources >= profile.max_web_sources:
        return ToolResult(
            success=False,
            error="web_sources_limit_reached",
            metadata={"limit": profile.max_web_sources},
        )
    policy = _domain_policy_from_env()
    if policy and not _url_allowed(args.url, policy):
        host = _normalize_host(args.url)
        return ToolResult(
            success=False,
            error="domain_blocked",
            metadata={"domain": host, "policy": policy, "untrusted": True},
            retryable=False,
        )
    try:
        resp = requests.get(
            args.url,
            headers={"User-Agent": "DrCodePT-Agent/1.0", **(args.headers or {})},
            timeout=args.timeout_seconds,
        )
        content = resp.content[: args.max_bytes]
        text = None
        try:
            text = content.decode(resp.encoding or "utf-8", errors="replace")
        except Exception:
            text = content.decode("utf-8", errors="replace")
        if args.strip_html:
            text = _strip_html(text)
        if usage:
            usage.consume_web()
        return ToolResult(
            success=True,
            output={
                "url": resp.url,
                "status_code": resp.status_code,
                "headers": dict(resp.headers),
                "text": text,
                "untrusted": True,
            },
            metadata={"untrusted": True},
        )
    except requests.RequestException as exc:
        return ToolResult(success=False, error=str(exc), retryable=True, metadata={"untrusted": True})


class WebSearchArgs(BaseModel):
    query: str
    max_results: int = 5
    region: str = "us-en"
    timeout_seconds: int = 15
    max_bytes: int = 1_000_000


def _strip_html(text: str) -> str:
    if not text:
        return ""
    cleaned = re.sub(r"<[^>]+>", " ", text)
    cleaned = html_lib.unescape(cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def _decode_ddg_url(href: str) -> str:
    if not href:
        return href
    if "uddg=" in href:
        parsed = urlparse(href)
        qs = parse_qs(parsed.query)
        if "uddg" in qs and qs["uddg"]:
            return unquote(qs["uddg"][0])
    return href


def _normalize_host(value: str) -> str:
    if not value:
        return ""
    value = value.strip().lower()
    if "://" in value:
        try:
            value = urlparse(value).netloc
        except Exception:
            pass
    if "@" in value:
        value = value.split("@")[-1]
    if ":" in value:
        value = value.split(":", 1)[0]
    if value.startswith("www."):
        value = value[4:]
    return value.strip(".")


def _split_domains(raw: str) -> List[str]:
    if not raw:
        return []
    items: List[str] = []
    for token in re.split(r"[,\s]+", raw):
        if not token:
            continue
        host = _normalize_host(token)
        if host and host not in items:
            items.append(host)
    return items


def _split_suffixes(raw: str) -> List[str]:
    if not raw:
        return []
    items: List[str] = []
    for token in re.split(r"[,\s]+", raw):
        tok = token.strip().lower()
        if not tok:
            continue
        if not tok.startswith("."):
            tok = "." + tok
        if tok not in items:
            items.append(tok)
    return items


def _match_domain(host: str, domain: str) -> bool:
    if not host or not domain:
        return False
    return host == domain or host.endswith("." + domain)


def _domain_policy_from_env() -> Optional[Dict[str, List[str]]]:
    allow_domains = _split_domains(os.getenv("TREYS_AGENT_WEB_ALLOWLIST", ""))
    allow_suffixes = _split_suffixes(os.getenv("TREYS_AGENT_WEB_ALLOW_SUFFIXES", ""))
    block_domains = _split_domains(os.getenv("TREYS_AGENT_WEB_BLOCKLIST", ""))
    block_suffixes = _split_suffixes(os.getenv("TREYS_AGENT_WEB_BLOCK_SUFFIXES", ""))
    if not (allow_domains or allow_suffixes or block_domains or block_suffixes):
        return None
    return {
        "allow_domains": allow_domains,
        "allow_suffixes": allow_suffixes,
        "block_domains": block_domains,
        "block_suffixes": block_suffixes,
    }


def _url_allowed(url: str, policy: Dict[str, List[str]]) -> bool:
    host = _normalize_host(url)
    if not host:
        return False
    for blocked in policy.get("block_domains", []):
        if _match_domain(host, blocked):
            return False
    for blocked_suffix in policy.get("block_suffixes", []):
        if host.endswith(blocked_suffix):
            return False
    allow_domains = policy.get("allow_domains", [])
    allow_suffixes = policy.get("allow_suffixes", [])
    if allow_domains or allow_suffixes:
        for allowed in allow_domains:
            if _match_domain(host, allowed):
                return True
        for allowed_suffix in allow_suffixes:
            if host.endswith(allowed_suffix):
                return True
        return False
    return True


def web_search(ctx: RunContext, args: WebSearchArgs) -> ToolResult:
    profile = _get_profile(ctx)
    usage = _get_usage(ctx)
    if profile and usage and usage.web_sources >= profile.max_web_sources:
        return ToolResult(
            success=False,
            error="web_sources_limit_reached",
            metadata={"limit": profile.max_web_sources},
        )
    query = (args.query or "").strip()
    if not query:
        return ToolResult(success=False, error="query is required")
    url = "https://duckduckgo.com/html/"
    last_error: Optional[str] = None
    text = ""

    def _fetch() -> str:
        resp = requests.get(
            url,
            params={"q": query, "kl": args.region},
            headers={"User-Agent": "DrCodePT-Agent/1.0"},
            timeout=args.timeout_seconds,
        )
        content = resp.content[: args.max_bytes]
        return content.decode(resp.encoding or "utf-8", errors="replace")

    try:
        text = retry_with_backoff(
            _fetch,
            max_attempts=WEB_RETRY_CONFIG.max_attempts,
            initial_delay=WEB_RETRY_CONFIG.initial_delay,
            max_delay=WEB_RETRY_CONFIG.max_delay,
            backoff_factor=WEB_RETRY_CONFIG.backoff_factor,
            transient_exceptions=(requests.RequestException,),
        )
    except requests.RequestException as exc:
        last_error = str(exc)

    if last_error:
        return ToolResult(success=False, error=last_error, retryable=True, metadata={"untrusted": True})

    link_re = re.compile(r'<a[^>]+class="[^"]*result__a[^"]*"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', re.S)
    snippet_re = re.compile(r'class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</(?:a|div|span|p)>', re.S)

    links = link_re.findall(text)
    snippets = [_strip_html(s) for s in snippet_re.findall(text)]
    results: List[Dict[str, Any]] = []
    for idx, (href, title_html) in enumerate(links):
        if len(results) >= max(1, args.max_results):
            break
        title = _strip_html(title_html)
        url_out = _decode_ddg_url(href)
        snippet = snippets[idx] if idx < len(snippets) else ""
        results.append({"title": title, "url": url_out, "snippet": snippet})

    policy = _domain_policy_from_env()
    filtered_out = 0
    if policy:
        filtered: List[Dict[str, Any]] = []
        for item in results:
            url_out = (item or {}).get("url") or ""
            if _url_allowed(url_out, policy):
                filtered.append(item)
            else:
                filtered_out += 1
        results = filtered

    warning = None
    if not results:
        warning = "filtered_no_results" if filtered_out else "no_results"
    elif len(results) < max(1, args.max_results // 2):
        warning = "weak_results"
    elif filtered_out:
        warning = "filtered_results"
    if usage:
        usage.consume_web()
    if warning in {"no_results", "filtered_no_results"}:
        return ToolResult(
            success=False,
            error="no_results",
            output={
                "query": query,
                "region": args.region,
                "result_count": len(results),
                "results": results,
                "source": "duckduckgo_html",
                "warning": warning,
                "filtered_out": filtered_out,
                "untrusted": True,
            },
            metadata={"untrusted": True},
        )
    return ToolResult(
        success=True,
        output={
            "query": query,
            "region": args.region,
            "result_count": len(results),
            "results": results,
            "source": "duckduckgo_html",
            "warning": warning,
            "filtered_out": filtered_out,
            "untrusted": True,
        },
        metadata={"untrusted": True},
    )


class RepoScanArgs(BaseModel):
    repo_root: Optional[str] = None


def scan_repo(repo_root: Optional[str] = None) -> Dict[str, Any]:
    """Scan repository and produce repo_map.json.

    This tool scans the repository structure and identifies key files
    without reading everything. It produces:
    - repo_index.json: All files with metadata
    - repo_map.json: Key files only

    Args:
        repo_root: Root directory to scan (default: current directory)

    Returns:
        Dict with scan results
    """
    from agent.autonomous.tools.repo_scanner import RepoScanner

    if repo_root is None:
        repo_root = os.getcwd()

    repo_root = Path(repo_root)

    try:
        scanner = RepoScanner(repo_root, max_files=500, max_bytes=10_000_000)
        index, map_obj = scanner.scan()

        return {
            "success": True,
            "index": {
                "total_files": index.total_files,
                "total_bytes": index.total_bytes,
                "files": [
                    {
                        "path": f.path,
                        "size_bytes": f.size_bytes,
                        "file_type": f.file_type,
                    }
                    for f in index.files[:20]
                ],
            },
            "map": {
                "key_files": [
                    {
                        "path": f.path,
                        "reason": f.reason,
                    }
                    for f in map_obj.key_files
                ],
                "structure": map_obj.structure_summary,
            },
        }

    except Exception as exc:
        logger.error(f"Error scanning repository: {exc}", exc_info=True)
        return {
            "success": False,
            "error": str(exc),
        }


def scan_repo_tool(ctx: RunContext, args: RepoScanArgs) -> ToolResult:
    payload = scan_repo(args.repo_root)
    if payload.get("success"):
        return ToolResult(success=True, output=payload)
    return ToolResult(success=False, error=payload.get("error") or "scan_failed", output=payload)


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


class FileReadArgs(BaseModel):
    path: str
    max_bytes: int = 1_000_000


def file_read_factory(agent_cfg: AgentConfig):
    def file_read(ctx: RunContext, args: FileReadArgs) -> ToolResult:
        profile = _get_profile(ctx)
        usage = _get_usage(ctx)
        path = Path(args.path)
        if not path.is_absolute():
            path = (ctx.workspace_dir / path).resolve()
        if not _fs_allowed(path, agent_cfg, ctx):
            return ToolResult(
                success=False,
                error=f"Read blocked outside allowed roots: {path}",
                metadata={
                    "unsafe_blocked": True,
                    "workspace_dir": str(ctx.workspace_dir),
                    "allowed_roots": [str(r) for r in agent_cfg.fs_allowed_roots],
                },
            )
        if not path.exists():
            return ToolResult(success=False, error=f"File not found: {path}")
        if profile and usage:
            if not usage.can_read_file(profile.max_files_to_read):
                return ToolResult(
                    success=False,
                    error="file_read_limit_reached",
                    metadata={"limit": profile.max_files_to_read},
                )
            remaining = usage.remaining_bytes(profile.max_total_bytes_to_read)
            if remaining <= 0:
                return ToolResult(
                    success=False,
                    error="file_read_bytes_limit_reached",
                    metadata={"limit": profile.max_total_bytes_to_read},
                )
            read_cap = min(args.max_bytes, remaining)
        else:
            read_cap = args.max_bytes
        data = path.read_bytes()[:read_cap]
        if profile and usage:
            usage.consume_file(len(data))
        return ToolResult(success=True, output={"path": str(path), "content": data.decode("utf-8", errors="replace")})

    return file_read


class FileWriteArgs(BaseModel):
    path: str
    content: str
    mode: str = "overwrite"  # overwrite | append


def file_write_factory(agent_cfg: AgentConfig):
    def file_write(ctx: RunContext, args: FileWriteArgs) -> ToolResult:
        path = Path(args.path)
        if not path.is_absolute():
            path = (ctx.workspace_dir / path).resolve()

        if not _fs_allowed(path, agent_cfg, ctx):
            return ToolResult(
                success=False,
                error=f"Write blocked outside allowed roots: {path}",
                metadata={
                    "unsafe_blocked": True,
                    "workspace_dir": str(ctx.workspace_dir),
                    "allowed_roots": [str(r) for r in agent_cfg.fs_allowed_roots],
                },
            )

        path.parent.mkdir(parents=True, exist_ok=True)
        if args.mode == "append":
            with path.open("a", encoding="utf-8", errors="replace", newline="\n") as f:
                f.write(args.content)
        else:
            path.write_text(args.content, encoding="utf-8", errors="replace")
        return ToolResult(success=True, output={"path": str(path), "bytes": len(args.content.encode("utf-8"))})

    return file_write


class ListDirArgs(BaseModel):
    path: str = "."
    max_entries: int = 200
    include_hidden: bool = False


def list_dir_factory(agent_cfg: AgentConfig):
    def list_dir(ctx: RunContext, args: ListDirArgs) -> ToolResult:
        profile = _get_profile(ctx)
        path = Path(args.path)
        if not path.is_absolute():
            path = (ctx.workspace_dir / path).resolve()
        if not _fs_allowed(path, agent_cfg, ctx):
            return ToolResult(
                success=False,
                error=f"List blocked outside allowed roots: {path}",
                metadata={
                    "unsafe_blocked": True,
                    "workspace_dir": str(ctx.workspace_dir),
                    "allowed_roots": [str(r) for r in agent_cfg.fs_allowed_roots],
                },
            )
        if not path.exists():
            return ToolResult(success=False, error=f"Directory not found: {path}")
        if not path.is_dir():
            return ToolResult(success=False, error=f"Not a directory: {path}")
        items: List[Dict[str, Any]] = []
        count = 0
        effective_max = args.max_entries
        if profile:
            effective_max = _cap_results(effective_max, profile.max_glob_results)
        for entry in path.iterdir():
            if not args.include_hidden and entry.name.startswith("."):
                continue
            try:
                stat = entry.stat()
                items.append(
                    {
                        "name": entry.name,
                        "path": str(entry),
                        "is_dir": entry.is_dir(),
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    }
                )
            except Exception:
                items.append({"name": entry.name, "path": str(entry), "is_dir": entry.is_dir()})
            count += 1
            if count >= max(1, effective_max):
                break
        return ToolResult(success=True, output={"path": str(path), "entries": items})

    return list_dir


class GlobArgs(BaseModel):
    root: str = "."
    pattern: str = "**/*"
    max_results: int = 200


def glob_paths_factory(agent_cfg: AgentConfig):
    def glob_paths(ctx: RunContext, args: GlobArgs) -> ToolResult:
        profile = _get_profile(ctx)
        usage = _get_usage(ctx)
        root = Path(args.root)
        if not root.is_absolute():
            root = (ctx.workspace_dir / root).resolve()
        if not _fs_allowed(root, agent_cfg, ctx):
            return ToolResult(
                success=False,
                error=f"Glob blocked outside allowed roots: {root}",
                metadata={
                    "unsafe_blocked": True,
                    "workspace_dir": str(ctx.workspace_dir),
                    "allowed_roots": [str(r) for r in agent_cfg.fs_allowed_roots],
                },
            )
        if not root.exists():
            return ToolResult(success=False, error=f"Root not found: {root}")
        results: List[str] = []
        effective_max = args.max_results
        if profile:
            effective_max = _cap_results(effective_max, profile.max_glob_results)
        for path in root.glob(args.pattern):
            results.append(str(path))
            if len(results) >= max(1, effective_max):
                break
        if usage:
            usage.consume_glob(len(results))
        return ToolResult(success=True, output={"root": str(root), "pattern": args.pattern, "results": results})

    return glob_paths


class FileSearchArgs(BaseModel):
    root: str = "."
    query: str
    case_sensitive: bool = False
    max_results: int = 50
    max_bytes: int = 1_000_000


def file_search_factory(agent_cfg: AgentConfig):
    def file_search(ctx: RunContext, args: FileSearchArgs) -> ToolResult:
        profile = _get_profile(ctx)
        usage = _get_usage(ctx)
        root = Path(args.root)
        if not root.is_absolute():
            root = (ctx.workspace_dir / root).resolve()
        if not _fs_allowed(root, agent_cfg, ctx):
            return ToolResult(
                success=False,
                error=f"Search blocked outside allowed roots: {root}",
                metadata={
                    "unsafe_blocked": True,
                    "workspace_dir": str(ctx.workspace_dir),
                    "allowed_roots": [str(r) for r in agent_cfg.fs_allowed_roots],
                },
            )
        if not root.exists():
            return ToolResult(success=False, error=f"Root not found: {root}")
        needle = args.query if args.case_sensitive else args.query.lower()
        hits: List[Dict[str, Any]] = []
        scanned = 0
        max_scan = profile.max_glob_results if profile else None
        skip_dirs = {
            "__pycache__",
            ".git",
            "node_modules",
            ".venv",
            "venv",
            "dist",
            "build",
        }
        binary_exts = {
            ".pyc",
            ".pyo",
            ".so",
            ".dll",
            ".exe",
            ".bin",
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".pdf",
            ".zip",
            ".tar",
            ".gz",
            ".7z",
            ".mp3",
            ".mp4",
            ".mov",
            ".avi",
            ".wav",
            ".flac",
            ".woff",
            ".woff2",
            ".ttf",
            ".otf",
            ".ico",
        }
        stop_scan = False
        for current_root, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in skip_dirs]
            for filename in filenames:
                if max_scan is not None and scanned >= max_scan:
                    stop_scan = True
                    break
                path = Path(current_root) / filename
                if path.suffix.lower() in binary_exts:
                    continue
                try:
                    if path.stat().st_size > args.max_bytes:
                        continue
                    if profile and usage:
                        if not usage.can_read_file(profile.max_files_to_read):
                            stop_scan = True
                            break
                        remaining = usage.remaining_bytes(profile.max_total_bytes_to_read)
                        if remaining <= 0:
                            stop_scan = True
                            break
                        read_cap = min(args.max_bytes, remaining)
                    else:
                        read_cap = args.max_bytes
                    data_bytes = path.read_bytes()[:read_cap]
                    if b"\x00" in data_bytes:
                        continue
                    try:
                        data = data_bytes.decode("utf-8")
                    except UnicodeDecodeError:
                        try:
                            data = data_bytes.decode("latin-1")
                        except Exception:
                            continue
                    if profile and usage:
                        usage.consume_file(len(data_bytes))
                except Exception:
                    continue
                hay = data if args.case_sensitive else data.lower()
                if needle in hay:
                    hits.append({"path": str(path), "preview": data[:300]})
                    if len(hits) >= max(1, args.max_results):
                        stop_scan = True
                        break
                scanned += 1
            if stop_scan:
                break
        return ToolResult(success=True, output={"root": str(root), "query": args.query, "matches": hits})

    return file_search


class FileCopyArgs(BaseModel):
    src: str
    dest: str


def file_copy_factory(agent_cfg: AgentConfig):
    def file_copy(ctx: RunContext, args: FileCopyArgs) -> ToolResult:
        src = Path(args.src)
        if not src.is_absolute():
            src = (Path.cwd() / src).resolve()
        dest = Path(args.dest)
        if not dest.is_absolute():
            dest = (ctx.workspace_dir / dest).resolve()

        if not _fs_allowed(src, agent_cfg, ctx) or not _fs_allowed(dest, agent_cfg, ctx):
            return ToolResult(
                success=False,
                error=f"Copy blocked outside allowed roots: {src} -> {dest}",
                metadata={
                    "unsafe_blocked": True,
                    "workspace_dir": str(ctx.workspace_dir),
                    "allowed_roots": [str(r) for r in agent_cfg.fs_allowed_roots],
                },
            )
        if not src.exists():
            return ToolResult(success=False, error=f"Source not found: {src}")

        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            if src.is_dir():
                shutil.copytree(src, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dest)
            return ToolResult(success=True, output={"src": str(src), "dest": str(dest)})
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))

    return file_copy


class FileMoveArgs(BaseModel):
    src: str
    dest: str


def file_move_factory(agent_cfg: AgentConfig):
    def file_move(ctx: RunContext, args: FileMoveArgs) -> ToolResult:
        src = Path(args.src)
        if not src.is_absolute():
            src = (Path.cwd() / src).resolve()
        dest = Path(args.dest)
        if not dest.is_absolute():
            dest = (ctx.workspace_dir / dest).resolve()

        if not _fs_allowed(dest, agent_cfg, ctx) or not _fs_allowed(src, agent_cfg, ctx):
            return ToolResult(
                success=False,
                error=f"Move blocked outside allowed roots: {src} -> {dest}",
                metadata={
                    "unsafe_blocked": True,
                    "approval_required": True,
                    "workspace_dir": str(ctx.workspace_dir),
                    "allowed_roots": [str(r) for r in agent_cfg.fs_allowed_roots],
                },
            )
        if not src.exists():
            return ToolResult(success=False, error=f"Source not found: {src}")

        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.move(str(src), str(dest))
            return ToolResult(success=True, output={"src": str(src), "dest": str(dest)})
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))

    return file_move


class FileDeleteArgs(BaseModel):
    path: str


def file_delete_factory(agent_cfg: AgentConfig):
    def file_delete(ctx: RunContext, args: FileDeleteArgs) -> ToolResult:
        path = Path(args.path)
        if not path.is_absolute():
            path = (ctx.workspace_dir / path).resolve()

        if not _fs_allowed(path, agent_cfg, ctx):
            return ToolResult(
                success=False,
                error=f"Delete blocked outside allowed roots: {path}",
                metadata={
                    "unsafe_blocked": True,
                    "approval_required": True,
                    "workspace_dir": str(ctx.workspace_dir),
                    "allowed_roots": [str(r) for r in agent_cfg.fs_allowed_roots],
                },
            )
        if not path.exists():
            return ToolResult(success=False, error=f"Path not found: {path}")
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            return ToolResult(success=True, output={"deleted": str(path)})
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))

    return file_delete


class ZipExtractArgs(BaseModel):
    zip_path: str
    dest_dir: str


def zip_extract_factory(agent_cfg: AgentConfig):
    def zip_extract(ctx: RunContext, args: ZipExtractArgs) -> ToolResult:
        zip_path = Path(args.zip_path)
        if not zip_path.is_absolute():
            zip_path = (Path.cwd() / zip_path).resolve()
        dest = Path(args.dest_dir)
        if not dest.is_absolute():
            dest = (ctx.workspace_dir / dest).resolve()

        if not _fs_allowed(zip_path, agent_cfg, ctx) or not _fs_allowed(dest, agent_cfg, ctx):
            return ToolResult(
                success=False,
                error=f"Extract blocked outside allowed roots: {zip_path} -> {dest}",
                metadata={
                    "unsafe_blocked": True,
                    "workspace_dir": str(ctx.workspace_dir),
                    "allowed_roots": [str(r) for r in agent_cfg.fs_allowed_roots],
                },
            )
        if not zip_path.exists():
            return ToolResult(success=False, error=f"Zip not found: {zip_path}")

        dest.mkdir(parents=True, exist_ok=True)
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(dest)
            return ToolResult(success=True, output={"zip": str(zip_path), "dest": str(dest)})
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))

    return zip_extract


class ZipCreateArgs(BaseModel):
    src: str
    zip_path: str


def zip_create_factory(agent_cfg: AgentConfig):
    def zip_create(ctx: RunContext, args: ZipCreateArgs) -> ToolResult:
        src = Path(args.src)
        if not src.is_absolute():
            src = (Path.cwd() / src).resolve()
        zip_path = Path(args.zip_path)
        if not zip_path.is_absolute():
            zip_path = (ctx.workspace_dir / zip_path).resolve()

        if not _fs_allowed(src, agent_cfg, ctx) or not _fs_allowed(zip_path, agent_cfg, ctx):
            return ToolResult(
                success=False,
                error=f"Zip create blocked outside allowed roots: {src} -> {zip_path}",
                metadata={
                    "unsafe_blocked": True,
                    "workspace_dir": str(ctx.workspace_dir),
                    "allowed_roots": [str(r) for r in agent_cfg.fs_allowed_roots],
                },
            )
        if not src.exists():
            return ToolResult(success=False, error=f"Source not found: {src}")

        zip_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                if src.is_dir():
                    for file in src.rglob("*"):
                        if file.is_file():
                            zf.write(file, file.relative_to(src))
                else:
                    zf.write(src, src.name)
            return ToolResult(success=True, output={"src": str(src), "zip": str(zip_path)})
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))

    return zip_create


class ClipboardGetArgs(BaseModel):
    pass


def clipboard_get(ctx: RunContext, args: ClipboardGetArgs) -> ToolResult:
    try:
        text = subprocess.check_output(
            ["powershell", "-NoLogo", "-NoProfile", "-Command", "Get-Clipboard -Raw"],
            text=True,
        )
        return ToolResult(success=True, output={"text": text})
    except Exception as exc:
        return ToolResult(success=False, error=str(exc))


class ClipboardSetArgs(BaseModel):
    text: str


def clipboard_set(ctx: RunContext, args: ClipboardSetArgs) -> ToolResult:
    try:
        subprocess.run(
            ["powershell", "-NoLogo", "-NoProfile", "-Command", "Set-Clipboard"],
            input=args.text,
            text=True,
            capture_output=True,
            check=True,
        )
        return ToolResult(success=True, output={"bytes": len(args.text.encode("utf-8"))})
    except Exception as exc:
        return ToolResult(success=False, error=str(exc))


class SystemInfoArgs(BaseModel):
    pass


def system_info(ctx: RunContext, args: SystemInfoArgs) -> ToolResult:
    info = {
        "platform": platform.platform(),
        "python": sys.version,
        "cwd": str(Path.cwd()),
        "user": os.getenv("USERNAME") or os.getenv("USER") or "",
        "timezone": "UTC"
    }
    # Try to get real timezone on Windows via PowerShell
    if platform.system() == "Windows":
        try:
            tz = subprocess.check_output(
                ["powershell", "-NoLogo", "-NoProfile", "-Command", "[System.TimeZoneInfo]::Local.Id"],
                text=True,
            ).strip()
            if tz:
                info["timezone"] = tz
        except Exception:
            pass
    return ToolResult(success=True, output=info)


class PythonExecArgs(BaseModel):
    code: str
    timeout_seconds: int = 20
    allow_network: bool = True
    allowed_imports: List[str] = Field(default_factory=list)


def python_exec_factory(agent_cfg: AgentConfig):
    def python_exec(ctx: RunContext, args: PythonExecArgs) -> ToolResult:
        tmp = ctx.workspace_dir / f"python_exec_{int(time.time()*1000)}.py"
        tmp.write_text(args.code, encoding="utf-8")
        try:
            proc = subprocess.run(
                [sys.executable, str(tmp)],
                cwd=str(ctx.workspace_dir),
                capture_output=True,
                text=True,
                timeout=args.timeout_seconds,
            )
            return ToolResult(
                success=proc.returncode == 0,
                output={"exit_code": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr},
                error=None if proc.returncode == 0 else (proc.stderr.strip() or f"exit_code={proc.returncode}"),
            )
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, error="python_exec timeout", retryable=True)

    return python_exec


class HumanAskArgs(BaseModel):
    question: str


def human_ask_factory(cfg: AgentConfig):
    def human_ask(ctx: RunContext, args: HumanAskArgs) -> ToolResult:
        auto_answer = os.getenv("AGENT_AUTO_ANSWER")
        auto_approve = os.getenv("AGENT_AUTO_APPROVE", "")
        if auto_answer is not None:
            answer = auto_answer.strip()
            print(f"\n[HUMAN INPUT AUTO]\n{args.question}\n> {answer}")
            return ToolResult(success=True, output={"answer": answer, "auto": True})
        if auto_approve.lower() in {"1", "true", "yes", "y"}:
            answer = "yes"
            print(f"\n[HUMAN INPUT AUTO]\n{args.question}\n> {answer}")
            return ToolResult(success=True, output={"answer": answer, "auto": True})
        answer = input(f"\n[HUMAN INPUT NEEDED]\n{args.question}\n> ").strip()
        return ToolResult(success=True, output={"answer": answer})

    return human_ask


class FinishArgs(BaseModel):
    summary: str = ""


def finish(ctx: RunContext, args: FinishArgs) -> ToolResult:
    _close_web_session(ctx)
    return ToolResult(success=True, output={"summary": args.summary})


class DelegateTaskArgs(BaseModel):
    task: str
    max_steps: int = 20
    timeout_seconds: int = 600
    planner_mode: str = "auto"  # react | plan_first | auto
    num_candidates: int = 1
    max_plan_steps: int = 6
    use_dppm: bool = True
    use_tot: bool = True


def delegate_task_factory(agent_cfg: AgentConfig, memory_store: Optional[SqliteMemoryStore]):
    def delegate_task(ctx: RunContext, args: DelegateTaskArgs) -> ToolResult:
        task = (args.task or "").strip()
        if not task:
            return ToolResult(success=False, error="delegate_task requires task")
        try:
            from agent.autonomous.config import PlannerConfig, RunnerConfig
            from agent.autonomous.runner import AgentRunner
            from agent.llm import CodexCliAuthError, CodexCliClient, CodexCliNotFoundError
        except Exception as exc:
            return ToolResult(success=False, error=f"delegate_task import failed: {exc}")

        mode = (args.planner_mode or "react").strip().lower()
        if mode == "auto":
            mode = _choose_planner_mode(task)
        if mode not in {"react", "plan_first"}:
            mode = "react"

        try:
            llm = CodexCliClient.from_env()
        except (CodexCliNotFoundError, CodexCliAuthError) as exc:
            return ToolResult(success=False, error=str(exc))
        except Exception as exc:
            return ToolResult(success=False, error=f"delegate_task llm error: {exc}")

        run_id = f"delegate_{int(time.time())}_{uuid4().hex[:8]}"
        run_dir = ctx.run_dir / "delegates" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        runner = AgentRunner(
            cfg=RunnerConfig(max_steps=max(1, int(args.max_steps)), timeout_seconds=max(30, int(args.timeout_seconds))),
            agent_cfg=agent_cfg,
            planner_cfg=PlannerConfig(
                mode=mode,  # type: ignore[arg-type]
                num_candidates=max(1, int(args.num_candidates)),
                max_plan_steps=max(1, int(args.max_plan_steps)),
                use_dppm=bool(args.use_dppm),
                use_tot=bool(args.use_tot),
            ),
            llm=llm,
            run_dir=run_dir,
            memory_store=memory_store,
        )
        result = runner.run(task)
        return ToolResult(
            success=result.success,
            output={
                "task": task,
                "run_id": result.run_id,
                "trace_path": result.trace_path,
                "stop_reason": result.stop_reason,
                "steps_executed": result.steps_executed,
                "planner_mode": mode,
            },
            error=None if result.success else f"delegate_task stopped: {result.stop_reason}",
        )

    return delegate_task


class MemoryStoreArgs(BaseModel):
    kind: MemoryKind = "knowledge"
    key: Optional[str] = None
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


def memory_store_factory(agent_cfg: AgentConfig, store: Optional[SqliteMemoryStore]):
    def memory_store(ctx: RunContext, args: MemoryStoreArgs) -> ToolResult:
        if store is None:
            return ToolResult(success=False, error="Memory store not configured")
        if args.kind == "user_info" and not agent_cfg.allow_user_info_storage:
            return ToolResult(
                success=False,
                error="user_info storage disabled (enable allow_user_info_storage to permit).",
                metadata={"unsafe_blocked": True},
            )
        rec_id = store.upsert(kind=args.kind, key=args.key, content=args.content, metadata=args.metadata)
        return ToolResult(success=True, output={"id": rec_id, "kind": args.kind})

    return memory_store


class MemorySearchArgs(BaseModel):
    query: str
    kinds: List[MemoryKind] = Field(default_factory=list)
    limit: int = 8


def memory_search_factory(store: Optional[SqliteMemoryStore]):
    def memory_search(ctx: RunContext, args: MemorySearchArgs) -> ToolResult:
        if store is None:
            return ToolResult(success=False, error="Memory store not configured")
        kinds = args.kinds or None
        results = store.search(args.query, kinds=kinds, limit=args.limit)
        return ToolResult(
            success=True,
            output={
                "results": [
                    {
                        "kind": r.kind,
                        "id": r.id,
                        "key": r.key,
                        "content": r.content,
                        "metadata": r.metadata,
                        "created_at": r.created_at,
                        "updated_at": r.updated_at,
                    }
                    for r in results
                ]
            },
        )

    return memory_search


class McpListArgs(BaseModel):
    server: Optional[str] = None


class McpCallArgs(BaseModel):
    server: Optional[str] = None
    tool: str
    args: Dict[str, Any] = Field(default_factory=dict)


def mcp_list_factory():
    def mcp_list(ctx: RunContext, args: McpListArgs) -> ToolResult:
        try:
            from agent.mcp.client import MCPClient
            from agent.mcp.registry import get_server
            from agent.mcp.state import get_active_server
        except Exception as exc:
            return ToolResult(success=False, error=f"mcp unavailable: {exc}")

        name = args.server or get_active_server()
        if not name:
            return ToolResult(success=False, error="mcp: no active server")
        server = get_server(name)
        if server is None:
            return ToolResult(success=False, error=f"mcp: unknown server {name}")
        resp = MCPClient(server).list_tools()
        if resp.error:
            return ToolResult(success=False, error=str(resp.error))
        return ToolResult(success=True, output=resp.result or {})

    return mcp_list


def mcp_call_factory():
    def mcp_call(ctx: RunContext, args: McpCallArgs) -> ToolResult:
        try:
            from agent.mcp.client import MCPClient
            from agent.mcp.registry import get_server
            from agent.mcp.state import get_active_server
        except Exception as exc:
            return ToolResult(success=False, error=f"mcp unavailable: {exc}")

        name = args.server or get_active_server()
        if not name:
            return ToolResult(success=False, error="mcp: no active server")
        server = get_server(name)
        if server is None:
            return ToolResult(success=False, error=f"mcp: unknown server {name}")
        resp = MCPClient(server).call_tool(args.tool, args.args or {})
        if resp.error:
            return ToolResult(success=False, error=str(resp.error))
        return ToolResult(success=True, output=resp.result or {})

    return mcp_call


class ShellExecArgs(BaseModel):
    command: str
    timeout_seconds: int = 30
    cwd: Optional[str] = None


def shell_exec_factory(agent_cfg: AgentConfig):
    def shell_exec(ctx: RunContext, args: ShellExecArgs) -> ToolResult:
        try:
            allowed, reason = _shell_allowed(args.command, unsafe_mode=agent_cfg.unsafe_mode)
            if not allowed:
                return ToolResult(
                    success=False,
                    error=f"shell_exec blocked: {reason}",
                    metadata={"unsafe_blocked": True, "command": args.command},
                )
            cwd_input = args.cwd or str(ctx.workspace_dir)
            cwd_path = Path(cwd_input)
            if not cwd_path.is_absolute():
                cwd_path = (ctx.workspace_dir / cwd_path).resolve()
            else:
                cwd_path = cwd_path.resolve()
            coerced = False
            if not _fs_allowed(cwd_path, agent_cfg, ctx):
                # Fall back to workspace if the requested cwd is outside allowed roots.
                if _fs_allowed(ctx.workspace_dir, agent_cfg, ctx):
                    cwd_path = ctx.workspace_dir
                    coerced = True
                else:
                    return ToolResult(
                        success=False,
                        error=f"shell_exec blocked outside allowed roots: {cwd_input}",
                        metadata={"unsafe_blocked": True, "cwd": cwd_input},
                    )
            proc = subprocess.run(
                args.command,
                cwd=str(cwd_path),
                capture_output=True,
                text=True,
                timeout=args.timeout_seconds,
                shell=True,
            )
            return ToolResult(
                success=proc.returncode == 0,
                output={"exit_code": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr},
                error=None if proc.returncode == 0 else (proc.stderr.strip() or f"exit_code={proc.returncode}"),
                metadata={"cwd": str(cwd_path), "cwd_coerced": coerced} if coerced else {"cwd": str(cwd_path)},
            )
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, error="shell_exec timeout", retryable=True)
    return shell_exec


class WebGuiSnapshotArgs(BaseModel):
    url: str
    timeout_ms: int = 15_000
    max_text_chars: int = 8_000
    include_screenshot: bool = False


def web_gui_snapshot(ctx: RunContext, args: WebGuiSnapshotArgs) -> ToolResult:  
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # pragma: no cover
        return ToolResult(success=False, error=f"Playwright unavailable: {exc}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(args.url, timeout=args.timeout_ms, wait_until="domcontentloaded")
            page.wait_for_timeout(250)

            url = page.url
            title = page.title()
            try:
                visible_text = page.inner_text("body")[: args.max_text_chars]
            except Exception:
                visible_text = ""
            try:
                a11y = page.accessibility.snapshot()
            except Exception:
                a11y = None
            try:
                html = page.content()
            except Exception:
                html = ""

            screenshot_path = None
            if args.include_screenshot:
                screenshot_path = str(ctx.run_dir / "web_gui_snapshot.png")
                try:
                    page.screenshot(path=screenshot_path, full_page=True)
                except Exception:
                    screenshot_path = None

            browser.close()
        return ToolResult(
            success=True,
            output={
                "url": url,
                "title": title,
                "visible_text": visible_text,
                "accessibility_tree": a11y,
                "html_preview": html[:4000],
                "screenshot": screenshot_path,
                "untrusted": True,
            },
            metadata={"untrusted": True},
        )
    except Exception as exc:
        return ToolResult(success=False, error=str(exc), retryable=True, metadata={"untrusted": True})


def _get_web_session(ctx: RunContext, *, headless: Optional[bool] = None) -> Dict[str, Any]:
    session = _WEB_SESSIONS.get(ctx.run_id)
    if session:
        return session
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"Playwright unavailable: {exc}") from exc

    pw = sync_playwright().start()
    launch_kwargs = {"headless": bool(headless) if headless is not None else True}
    browser = pw.chromium.launch(**launch_kwargs)
    context = browser.new_context()
    page = context.new_page()
    session = {"playwright": pw, "browser": browser, "context": context, "page": page, "elements": {}}
    _WEB_SESSIONS[ctx.run_id] = session
    return session


def _web_css_path_js() -> str:
    return """
    (el) => {
      if (!el || !el.tagName) return '';
      if (el.id) return '#' + el.id;
      const parts = [];
      while (el && el.nodeType === 1 && el.tagName.toLowerCase() !== 'html') {
        let selector = el.tagName.toLowerCase();
        if (el.className) {
          const cls = String(el.className).trim().split(/\\s+/).slice(0,2);
          if (cls.length) selector += '.' + cls.join('.');
        }
        const parent = el.parentNode;
        if (parent) {
          const siblings = Array.from(parent.children).filter(s => s.tagName === el.tagName);
          if (siblings.length > 1) {
            const index = siblings.indexOf(el) + 1;
            selector += `:nth-of-type(${index})`;
          }
        }
        parts.unshift(selector);
        el = parent;
      }
      parts.unshift('html');
      return parts.join(' > ');
    }
    """


def _close_web_session(ctx: RunContext) -> None:
    session = _WEB_SESSIONS.pop(ctx.run_id, None)
    if not session:
        return
    try:
        session.get("context") and session["context"].close()
    except Exception:
        pass
    try:
        session.get("browser") and session["browser"].close()
    except Exception:
        pass
    try:
        session.get("playwright") and session["playwright"].stop()
    except Exception:
        pass


class WebFindElementsArgs(BaseModel):
    query: str = ""
    url: Optional[str] = None
    role: Optional[str] = None
    name: Optional[str] = None
    text: Optional[str] = None
    css: Optional[str] = None
    limit: int = 10
    headless: Optional[bool] = None


def web_find_elements(ctx: RunContext, args: WebFindElementsArgs) -> ToolResult:
    try:
        session = _get_web_session(ctx, headless=args.headless)
        page = session["page"]
        if args.url:
            page.goto(args.url, wait_until="domcontentloaded")

        locators: List[Any] = []
        if args.css:
            locators.append(page.locator(args.css))
        if args.role:
            locators.append(page.get_by_role(args.role, name=args.name))
        if args.text:
            locators.append(page.get_by_text(args.text))
        if args.query and not (args.css or args.role or args.text):
            locators.append(page.get_by_text(args.query))

        elements: List[Dict[str, Any]] = []
        element_map: Dict[str, Dict[str, Any]] = session["elements"]
        idx = 0
        for locator in locators:
            count = locator.count()
            for i in range(min(count, max(1, args.limit))):
                handle = locator.nth(i)
                try:
                    selector = handle.evaluate(_web_css_path_js())
                except Exception:
                    selector = ""
                try:
                    role = handle.get_attribute("role") or handle.evaluate("el => el.tagName.toLowerCase()")
                except Exception:
                    role = ""
                try:
                    name = handle.get_attribute("aria-label") or ""
                except Exception:
                    name = ""
                try:
                    text = handle.inner_text() or ""
                except Exception:
                    text = ""
                try:
                    box = handle.bounding_box() or {}
                except Exception:
                    box = {}
                element_id = f"el_{idx}"
                idx += 1
                if selector:
                    element_map[element_id] = {"selector": selector}
                elements.append(
                    {
                        "element_id": element_id,
                        "role": role,
                        "name": name,
                        "text": text[:200],
                        "selector": selector,
                        "a11y_path": selector,
                        "bbox": box,
                    }
                )
                if len(elements) >= max(1, args.limit):
                    break
            if len(elements) >= max(1, args.limit):
                break

        return ToolResult(
            success=True,
            output={"url": page.url, "title": page.title(), "elements": elements},
        )
    except Exception as exc:
        return ToolResult(success=False, error=str(exc), retryable=True)


class WebClickArgs(BaseModel):
    element_id: Optional[str] = None
    selector: Optional[str] = None
    url: Optional[str] = None
    headless: Optional[bool] = None


def web_click(ctx: RunContext, args: WebClickArgs) -> ToolResult:
    try:
        session = _get_web_session(ctx, headless=args.headless)
        page = session["page"]
        if args.url:
            page.goto(args.url, wait_until="domcontentloaded")
        selector = args.selector
        if not selector and args.element_id:
            selector = (session["elements"].get(args.element_id) or {}).get("selector")
        if not selector:
            return ToolResult(success=False, error="web_click requires element_id or selector")
        page.locator(selector).first.click()
        shot_path = str(ctx.run_dir / f"web_click_{int(time.time())}.png")
        try:
            page.screenshot(path=shot_path, full_page=True)
        except Exception:
            shot_path = ""
        return ToolResult(success=True, output={"clicked": selector, "screenshot": shot_path})
    except Exception as exc:
        return ToolResult(success=False, error=str(exc), retryable=True)


class WebTypeArgs(BaseModel):
    element_id: Optional[str] = None
    selector: Optional[str] = None
    text: str
    url: Optional[str] = None
    headless: Optional[bool] = None


def web_type(ctx: RunContext, args: WebTypeArgs) -> ToolResult:
    try:
        session = _get_web_session(ctx, headless=args.headless)
        page = session["page"]
        if args.url:
            page.goto(args.url, wait_until="domcontentloaded")
        selector = args.selector
        if not selector and args.element_id:
            selector = (session["elements"].get(args.element_id) or {}).get("selector")
        if not selector:
            return ToolResult(success=False, error="web_type requires element_id or selector")
        page.locator(selector).first.fill(str(args.text))
        shot_path = str(ctx.run_dir / f"web_type_{int(time.time())}.png")
        try:
            page.screenshot(path=shot_path, full_page=True)
        except Exception:
            shot_path = ""
        return ToolResult(success=True, output={"typed": selector, "screenshot": shot_path})
    except Exception as exc:
        return ToolResult(success=False, error=str(exc), retryable=True)


class WebScrollArgs(BaseModel):
    delta_y: int = 800
    url: Optional[str] = None
    headless: Optional[bool] = None


def web_scroll(ctx: RunContext, args: WebScrollArgs) -> ToolResult:
    try:
        session = _get_web_session(ctx, headless=args.headless)
        page = session["page"]
        if args.url:
            page.goto(args.url, wait_until="domcontentloaded")
        page.mouse.wheel(0, int(args.delta_y))
        shot_path = str(ctx.run_dir / f"web_scroll_{int(time.time())}.png")
        try:
            page.screenshot(path=shot_path, full_page=True)
        except Exception:
            shot_path = ""
        return ToolResult(success=True, output={"scrolled": args.delta_y, "screenshot": shot_path})
    except Exception as exc:
        return ToolResult(success=False, error=str(exc), retryable=True)


class WebCloseModalArgs(BaseModel):
    headless: Optional[bool] = None


def web_close_modal(ctx: RunContext, args: WebCloseModalArgs) -> ToolResult:
    try:
        session = _get_web_session(ctx, headless=args.headless)
        page = session["page"]
        closed = False
        selectors = [
            "button[aria-label='Close']",
            "[role='dialog'] button:has-text('Close')",
            "[role='dialog'] button:has-text('No thanks')",
            "[role='dialog'] button:has-text('Dismiss')",
            "button:has-text('Close')",
            "button:has-text('No thanks')",
            "button:has-text('Dismiss')",
            "[aria-label='close']",
        ]
        for sel in selectors:
            try:
                loc = page.locator(sel).first
                if loc.is_visible():
                    loc.click()
                    closed = True
                    break
            except Exception:
                continue
        if not closed:
            try:
                page.keyboard.press("Escape")
                closed = True
            except Exception:
                pass
        shot_path = str(ctx.run_dir / f"web_modal_{int(time.time())}.png")
        try:
            page.screenshot(path=shot_path, full_page=True)
        except Exception:
            shot_path = ""
        return ToolResult(success=True, output={"closed": closed, "screenshot": shot_path})
    except Exception as exc:
        return ToolResult(success=False, error=str(exc), retryable=True)


class DesktopStubArgs(BaseModel):
    action: str
    params: Dict[str, Any] = Field(default_factory=dict)


def desktop_action(ctx: RunContext, args: DesktopStubArgs) -> ToolResult:
    try:
        import pyautogui
    except Exception as exc:
        return ToolResult(success=False, error=f"pyautogui unavailable: {exc}")

    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.05

    action = (args.action or "").lower().strip()
    params = args.params or {}

    try:
        if action == "screenshot":
            path = params.get("path") or str(ctx.run_dir / f"desktop_{int(time.time())}.png")
            pyautogui.screenshot(path)
            return ToolResult(success=True, output={"path": path})

        if action == "click":
            x = params.get("x")
            y = params.get("y")
            if x is not None and y is not None:
                pyautogui.click(int(x), int(y))
            else:
                pyautogui.click()
            return ToolResult(success=True, output={"action": "click"})

        if action == "double_click":
            x = params.get("x")
            y = params.get("y")
            if x is not None and y is not None:
                pyautogui.doubleClick(int(x), int(y))
            else:
                pyautogui.doubleClick()
            return ToolResult(success=True, output={"action": "double_click"})

        if action == "move_mouse":
            x = params.get("x")
            y = params.get("y")
            if x is None or y is None:
                return ToolResult(success=False, error="move_mouse requires x and y")
            pyautogui.moveTo(int(x), int(y))
            return ToolResult(success=True, output={"x": int(x), "y": int(y)})

        if action == "drag_mouse":
            x = params.get("x")
            y = params.get("y")
            duration = float(params.get("duration", 0.2))
            if x is None or y is None:
                return ToolResult(success=False, error="drag_mouse requires x and y")
            pyautogui.dragTo(int(x), int(y), duration=duration)
            return ToolResult(success=True, output={"x": int(x), "y": int(y), "duration": duration})

        if action == "scroll":
            clicks = int(params.get("clicks", 0))
            pyautogui.scroll(clicks)
            return ToolResult(success=True, output={"clicks": clicks})

        if action == "type_text":
            text = params.get("text", "")
            interval = float(params.get("interval", 0.02))
            pyautogui.write(str(text), interval=interval)
            return ToolResult(success=True, output={"chars": len(str(text))})

        if action == "press_key":
            key = params.get("key")
            if not key:
                return ToolResult(success=False, error="press_key requires key")
            pyautogui.press(str(key))
            return ToolResult(success=True, output={"key": str(key)})

        if action == "hotkey":
            keys = params.get("keys") or []
            if not isinstance(keys, list) or not keys:
                return ToolResult(success=False, error="hotkey requires keys list")
            pyautogui.hotkey(*[str(k) for k in keys])
            return ToolResult(success=True, output={"keys": [str(k) for k in keys]})

        if action == "get_mouse_position":
            x, y = pyautogui.position()
            return ToolResult(success=True, output={"x": int(x), "y": int(y)})

        if action == "get_screen_size":
            w, h = pyautogui.size()
            return ToolResult(success=True, output={"width": int(w), "height": int(h)})

        if action == "wait":
            seconds = float(params.get("seconds", 1))
            time.sleep(seconds)
            return ToolResult(success=True, output={"seconds": seconds})

        return ToolResult(success=False, error=f"Unsupported desktop action: {action}")
    except Exception as exc:
        return ToolResult(success=False, error=str(exc))
    except Exception as exc:
        return ToolResult(success=False, error=f"Failed to send message: {exc}")


class DesktopSomSnapshotArgs(BaseModel):
    path: Optional[str] = None
    max_labels: int = 60
    include_labeled_image: bool = True


def desktop_som_snapshot(ctx: RunContext, args: DesktopSomSnapshotArgs) -> ToolResult:
    try:
        import pyautogui
    except Exception as exc:
        return ToolResult(success=False, error=f"pyautogui unavailable: {exc}")

    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.05

    path = args.path or str(ctx.run_dir / f"desktop_som_{int(time.time())}.png")
    pyautogui.screenshot(path)

    labels: List[Dict[str, Any]] = []
    try:
        from PIL import Image, ImageDraw, ImageFont

        img = Image.open(path)
        draw = ImageDraw.Draw(img)
        width, height = img.size

        # OCR if available
        try:
            import pytesseract

            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            for i in range(len(data.get("text", []))):
                text = (data["text"][i] or "").strip()
                if not text:
                    continue
                x, y, w, h = (
                    int(data["left"][i]),
                    int(data["top"][i]),
                    int(data["width"][i]),
                    int(data["height"][i]),
                )
                labels.append(
                    {
                        "text": text[:60],
                        "bbox": {"x": x, "y": y, "width": w, "height": h},
                        "source": "ocr",
                    }
                )
        except Exception:
            pass

        # Heuristic regions (top bar, left pane, right pane, main area)
        heuristics = [
            (0, 0, width, int(height * 0.1), "Top bar"),
            (0, 0, int(width * 0.18), height, "Left pane"),
            (int(width * 0.82), 0, int(width * 0.18), height, "Right pane"),
            (0, int(height * 0.1), width, int(height * 0.8), "Main area"),
            (0, int(height * 0.9), width, int(height * 0.1), "Bottom bar"),
        ]
        for x, y, w, h, label in heuristics:
            labels.append({"text": label, "bbox": {"x": x, "y": y, "width": w, "height": h}, "source": "heuristic"})

        # Limit and assign label_ids
        labels = labels[: max(1, args.max_labels)]
        labeled = []
        for idx, item in enumerate(labels):
            label_id = _label_id(idx)
            bbox = item["bbox"]
            labeled.append(
                {
                    "label_id": label_id,
                    "text": item.get("text", ""),
                    "bbox": bbox,
                    "source": item.get("source", ""),
                }
            )
            if args.include_labeled_image:
                x = int(bbox.get("x", 0))
                y = int(bbox.get("y", 0))
                w = int(bbox.get("width", 0))
                h = int(bbox.get("height", 0))
                draw.rectangle([x, y, x + w, y + h], outline="red", width=2)
                draw.text((x + 2, y + 2), label_id, fill="red")

        labeled_path = ""
        if args.include_labeled_image:
            labeled_path = str(ctx.run_dir / f"desktop_som_labeled_{int(time.time())}.png")
            img.save(labeled_path)

        _DESKTOP_SOM_STATE[ctx.run_id] = {"labels": labeled, "screenshot": path, "labeled": labeled_path}
        return ToolResult(
            success=True,
            output={"screenshot": path, "labeled_screenshot": labeled_path, "labels": labeled},
        )
    except Exception as exc:
        return ToolResult(success=False, error=str(exc), retryable=True)


class DesktopClickArgs(BaseModel):
    label_id: str


def desktop_click(ctx: RunContext, args: DesktopClickArgs) -> ToolResult:
    try:
        import pyautogui
    except Exception as exc:
        return ToolResult(success=False, error=f"pyautogui unavailable: {exc}")

    state = _DESKTOP_SOM_STATE.get(ctx.run_id) or {}
    labels = state.get("labels") or []
    target = next((l for l in labels if l.get("label_id") == args.label_id), None)
    if not target:
        return ToolResult(success=False, error=f"Unknown label_id: {args.label_id}")
    bbox = target.get("bbox") or {}
    x = int(bbox.get("x", 0) + bbox.get("width", 0) / 2)
    y = int(bbox.get("y", 0) + bbox.get("height", 0) / 2)
    pyautogui.click(x, y)
    # Post-action verification screenshot
    shot = str(ctx.run_dir / f"desktop_click_{int(time.time())}.png")
    try:
        pyautogui.screenshot(shot)
    except Exception:
        shot = ""
    return ToolResult(success=True, output={"clicked": args.label_id, "x": x, "y": y, "screenshot": shot})


def build_default_tool_registry(cfg: AgentConfig, run_dir: Path, *, memory_store: Optional[SqliteMemoryStore] = None) -> ToolRegistry:
    workspace_dir = run_dir / "workspace"
    workspace_dir.mkdir(parents=True, exist_ok=True)

    reg = ToolRegistry(agent_cfg=cfg, allow_interactive_tools=cfg.allow_interactive_tools)
    reg.register(ToolSpec(name="web_fetch", args_model=WebFetchArgs, fn=web_fetch, description="HTTP GET (with timeouts, optional HTML stripping)"))
    reg.register(ToolSpec(name="web_search", args_model=WebSearchArgs, fn=web_search, description="Search the web (DuckDuckGo HTML)"))
    reg.register(ToolSpec(name="file_read", args_model=FileReadArgs, fn=file_read_factory(cfg), description="Read a file"))
    reg.register(
        ToolSpec(
            name="file_write",
            args_model=FileWriteArgs,
            fn=file_write_factory(cfg),
            description="Write a file",
        )
    )
    reg.register(ToolSpec(name="list_dir", args_model=ListDirArgs, fn=list_dir_factory(cfg), description="List directory entries"))
    reg.register(ToolSpec(name="glob_paths", args_model=GlobArgs, fn=glob_paths_factory(cfg), description="Find paths by glob pattern"))
    reg.register(ToolSpec(name="file_search", args_model=FileSearchArgs, fn=file_search_factory(cfg), description="Search text in files"))
    reg.register(
        ToolSpec(
            name="file_copy",
            args_model=FileCopyArgs,
            fn=file_copy_factory(cfg),
            description="Copy files/directories",
        )
    )
    reg.register(
        ToolSpec(
            name="file_move",
            args_model=FileMoveArgs,
            fn=file_move_factory(cfg),
            description="Move files/directories",
        )
    )
    reg.register(
        ToolSpec(
            name="file_delete",
            args_model=FileDeleteArgs,
            fn=file_delete_factory(cfg),
            description="Delete files/directories",
        )
    )
    reg.register(
        ToolSpec(
            name="zip_extract",
            args_model=ZipExtractArgs,
            fn=zip_extract_factory(cfg),
            description="Extract zip to a directory",
        )
    )
    reg.register(
        ToolSpec(
            name="zip_create",
            args_model=ZipCreateArgs,
            fn=zip_create_factory(cfg),
            description="Create zip from file/dir",
        )
    )
    reg.register(ToolSpec(name="clipboard_get", args_model=ClipboardGetArgs, fn=clipboard_get, description="Read clipboard"))
    reg.register(ToolSpec(name="clipboard_set", args_model=ClipboardSetArgs, fn=clipboard_set, description="Write clipboard"))
    reg.register(ToolSpec(name="system_info", args_model=SystemInfoArgs, fn=system_info, description="Basic system info"))
    reg.register(
        ToolSpec(
            name="python_exec",
            args_model=PythonExecArgs,
            fn=python_exec_factory(cfg),
            description="Run Python code in a subprocess (no sandbox)",
        )
    )
    reg.register(
        ToolSpec(
            name="human_ask",
            args_model=HumanAskArgs,
            fn=human_ask_factory(cfg),
            description="Ask a human for help",
            dangerous=True,
        )
    )
    reg.register(
        ToolSpec(
            name="scan_repo",
            args_model=RepoScanArgs,
            fn=scan_repo_tool,
            description="Scan repository structure and identify key files",
        )
    )
    reg.register(
        ToolSpec(
            name="memory_store",
            args_model=MemoryStoreArgs,
            fn=memory_store_factory(cfg, memory_store),
            description="Persist a memory record (experiences/procedures/knowledge)",
        )
    )
    reg.register(
        ToolSpec(
            name="memory_search",
            args_model=MemorySearchArgs,
            fn=memory_search_factory(memory_store),
            description="Search long-term memory (keyword + recency)",
        )
    )
    reg.register(
        ToolSpec(
            name="mcp_list_tools",
            args_model=McpListArgs,
            fn=mcp_list_factory(),
            description="List tools from active MCP server",
        )
    )
    reg.register(
        ToolSpec(
            name="mcp_call",
            args_model=McpCallArgs,
            fn=mcp_call_factory(),
            description="Call a tool on the active MCP server",
        )
    )
    reg.register(
        ToolSpec(
            name="delegate_task",
            args_model=DelegateTaskArgs,
            fn=delegate_task_factory(cfg, memory_store),
            description="Run a sub-agent on a delegated task",
        )
    )
    reg.register(ToolSpec(name="finish", args_model=FinishArgs, fn=finish, description="Stop successfully"))
    reg.register(
        ToolSpec(
            name="shell_exec",
            args_model=ShellExecArgs,
            fn=shell_exec_factory(cfg),
            description="Execute a shell command",
        )
    )
    try:
        from .mail import MailArgs, mail_tool

        reg.register(
            ToolSpec(
                name="mail",
                args_model=MailArgs,
                fn=mail_tool,
                description="Email via provider APIs (currently: yahoo IMAP/SMTP)",
            )
        )
    except Exception:
        pass

    try:
        from agent.integrations.calendar_helper import CalendarHelper
        from agent.integrations.tasks_helper import TasksHelper
        
        calendar_helper = CalendarHelper()
        tasks_helper = TasksHelper()
        register_calendar_tasks_tools(reg, calendar_helper, tasks_helper)
    except Exception as exc:
        logger.warning(f"Direct Calendar/Tasks tools registration FAILED: {exc}")

    try:
        from agent.mcp.client import MCPClient
        mcp_client = MCPClient()
        # Initialize other MCP servers if needed, but not calendar/tasks (we have direct tools)
        try:
            asyncio.run(mcp_client.initialize([]))
        except RuntimeError:
            pass
    except Exception as exc:
        logger.debug(f"[DEBUG] MCP client initialization skipped: {exc}")

    if cfg.enable_web_gui:
        reg.register(
            ToolSpec(
                name="web_gui_snapshot",
                args_model=WebGuiSnapshotArgs,
                fn=web_gui_snapshot,
                description="Capture url + visible text + a11y tree (Playwright)",
            )
        )
        reg.register(
            ToolSpec(
                name="web_find_elements",
                args_model=WebFindElementsArgs,
                fn=web_find_elements,
                description="Find DOM elements by query/role/text and return selectors",
            )
        )
        reg.register(
            ToolSpec(
                name="web_click",
                args_model=WebClickArgs,
                fn=web_click,
                description="Click a previously found element_id or selector",
            )
        )
        reg.register(
            ToolSpec(
                name="web_type",
                args_model=WebTypeArgs,
                fn=web_type,
                description="Type into a previously found element_id or selector",
            )
        )
        reg.register(
            ToolSpec(
                name="web_scroll",
                args_model=WebScrollArgs,
                fn=web_scroll,
                description="Scroll the current web page and capture a screenshot",
            )
        )
        reg.register(
            ToolSpec(
                name="web_close_modal",
                args_model=WebCloseModalArgs,
                fn=web_close_modal,
                description="Detect and close modal/overlay dialogs",
            )
        )

    if cfg.enable_desktop:
        reg.register(
            ToolSpec(
                name="desktop",
                args_model=DesktopStubArgs,
                fn=desktop_action,
                description="Desktop automation via PyAutoGUI",
            )
        )
        reg.register(
            ToolSpec(
                name="desktop_som_snapshot",
                args_model=DesktopSomSnapshotArgs,
                fn=desktop_som_snapshot,
                description="Capture desktop snapshot with labeled OCR/heuristic boxes",
            )
        )
        reg.register(
            ToolSpec(
                name="desktop_click",
                args_model=DesktopClickArgs,
                fn=desktop_click,
                description="Click a labeled box from desktop_som_snapshot",
            )
        )

    return reg
