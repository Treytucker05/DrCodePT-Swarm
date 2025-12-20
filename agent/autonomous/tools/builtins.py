from __future__ import annotations

import ast
import json
import os
import platform
import shutil
import subprocess
import sys
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import requests
from pydantic import BaseModel, Field

from ..config import AgentConfig, RunContext
from ..memory.sqlite_store import MemoryKind, SqliteMemoryStore
from ..models import ToolResult
from .registry import ToolRegistry, ToolSpec


def _is_within(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except Exception:
        return False


def _fs_allowed(path: Path, cfg: AgentConfig, ctx: RunContext) -> bool:
    if cfg.unsafe_mode or cfg.allow_fs_anywhere:
        return True
    roots = list(cfg.fs_allowed_roots or [])
    roots.append(ctx.workspace_dir)
    return any(_is_within(path, root) for root in roots)


class WebFetchArgs(BaseModel):
    url: str
    timeout_seconds: int = 15
    max_bytes: int = 1_000_000
    headers: Dict[str, str] = Field(default_factory=dict)


def web_fetch(ctx: RunContext, args: WebFetchArgs) -> ToolResult:
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
        return ToolResult(
            success=True,
            output={
                "url": resp.url,
                "status_code": resp.status_code,
                "headers": dict(resp.headers),
                "text": text,
            },
        )
    except requests.RequestException as exc:
        return ToolResult(success=False, error=str(exc), retryable=True)


class FileReadArgs(BaseModel):
    path: str
    max_bytes: int = 1_000_000


def file_read(ctx: RunContext, args: FileReadArgs) -> ToolResult:
    path = Path(args.path)
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    if not path.exists():
        return ToolResult(success=False, error=f"File not found: {path}")
    data = path.read_bytes()[: args.max_bytes]
    return ToolResult(success=True, output={"path": str(path), "content": data.decode("utf-8", errors="replace")})


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


def list_dir(ctx: RunContext, args: ListDirArgs) -> ToolResult:
    path = Path(args.path)
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    if not path.exists():
        return ToolResult(success=False, error=f"Directory not found: {path}")
    if not path.is_dir():
        return ToolResult(success=False, error=f"Not a directory: {path}")
    items: List[Dict[str, Any]] = []
    count = 0
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
        if count >= max(1, args.max_entries):
            break
    return ToolResult(success=True, output={"path": str(path), "entries": items})


class GlobArgs(BaseModel):
    root: str = "."
    pattern: str = "**/*"
    max_results: int = 200


def glob_paths(ctx: RunContext, args: GlobArgs) -> ToolResult:
    root = Path(args.root)
    if not root.is_absolute():
        root = (Path.cwd() / root).resolve()
    if not root.exists():
        return ToolResult(success=False, error=f"Root not found: {root}")
    results: List[str] = []
    for path in root.glob(args.pattern):
        results.append(str(path))
        if len(results) >= max(1, args.max_results):
            break
    return ToolResult(success=True, output={"root": str(root), "pattern": args.pattern, "results": results})


class FileSearchArgs(BaseModel):
    root: str = "."
    query: str
    case_sensitive: bool = False
    max_results: int = 50
    max_bytes: int = 1_000_000


def file_search(ctx: RunContext, args: FileSearchArgs) -> ToolResult:
    root = Path(args.root)
    if not root.is_absolute():
        root = (Path.cwd() / root).resolve()
    if not root.exists():
        return ToolResult(success=False, error=f"Root not found: {root}")
    needle = args.query if args.case_sensitive else args.query.lower()
    hits: List[Dict[str, Any]] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            if path.stat().st_size > args.max_bytes:
                continue
            data = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        hay = data if args.case_sensitive else data.lower()
        if needle in hay:
            hits.append({"path": str(path), "preview": data[:300]})
            if len(hits) >= max(1, args.max_results):
                break
    return ToolResult(success=True, output={"root": str(root), "query": args.query, "matches": hits})


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

        if not _fs_allowed(dest, agent_cfg, ctx):
            return ToolResult(
                success=False,
                error=f"Copy blocked outside workspace: {dest}",
                metadata={"unsafe_blocked": True, "workspace_dir": str(ctx.workspace_dir)},
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

        if not _fs_allowed(dest, agent_cfg, ctx):
            return ToolResult(
                success=False,
                error=f"Extract blocked outside allowed roots: {dest}",
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

        if not _fs_allowed(zip_path, agent_cfg, ctx):
            return ToolResult(
                success=False,
                error=f"Zip create blocked outside allowed roots: {zip_path}",
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
    }
    return ToolResult(success=True, output=info)


class PythonExecArgs(BaseModel):
    code: str
    timeout_seconds: int = 20
    allow_network: bool = False
    allowed_imports: List[str] = Field(default_factory=list)

_DEFAULT_SAFE_IMPORTS: Set[str] = {
    "math",
    "json",
    "re",
    "datetime",
    "time",
    "statistics",
    "itertools",
    "functools",
    "collections",
}

_BANNED_IMPORTS: Set[str] = {
    "os",
    "sys",
    "subprocess",
    "socket",
    "urllib",
    "requests",
    "http",
    "pathlib",
    "shutil",
    "ctypes",
    "importlib",
    "multiprocessing",
    "threading",
    "asyncio",
    "signal",
}

_BANNED_CALLS: Set[str] = {
    "__import__",
    "eval",
    "exec",
    "compile",
    "open",
    "input",
    "breakpoint",
}


def _validate_python_code(code: str, *, allow_network: bool, allowed_imports: Set[str]) -> Optional[str]:
    if len(code) > 100_000:
        return "code_too_large"
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return f"syntax_error: {exc}"

    class Visitor(ast.NodeVisitor):
        def __init__(self):
            self.errors: List[str] = []

        def visit_Import(self, node: ast.Import) -> Any:  # noqa: ANN401
            for alias in node.names:
                root = (alias.name or "").split(".")[0]
                if root in _BANNED_IMPORTS:
                    self.errors.append(f"banned_import:{root}")
                elif root not in allowed_imports:
                    self.errors.append(f"import_not_allowed:{root}")
            self.generic_visit(node)

        def visit_ImportFrom(self, node: ast.ImportFrom) -> Any:  # noqa: ANN401
            root = (node.module or "").split(".")[0]
            if root in _BANNED_IMPORTS:
                self.errors.append(f"banned_import:{root}")
            elif root and root not in allowed_imports:
                self.errors.append(f"import_not_allowed:{root}")
            self.generic_visit(node)

        def visit_Call(self, node: ast.Call) -> Any:  # noqa: ANN401
            if isinstance(node.func, ast.Name) and node.func.id in _BANNED_CALLS:
                self.errors.append(f"banned_call:{node.func.id}")
            self.generic_visit(node)

        def visit_Attribute(self, node: ast.Attribute) -> Any:  # noqa: ANN401
            if node.attr.startswith("__"):
                self.errors.append("dunder_attribute_access")
            self.generic_visit(node)

    v = Visitor()
    v.visit(tree)
    if v.errors:
        return ",".join(sorted(set(v.errors)))
    if allow_network:
        # Best-effort: if caller explicitly wants network, require unsafe_mode at the tool layer.
        pass
    return None


def python_exec_factory(agent_cfg: AgentConfig):
    def python_exec(ctx: RunContext, args: PythonExecArgs) -> ToolResult:
        if args.allow_network and not agent_cfg.unsafe_mode:
            return ToolResult(
                success=False,
                error="python_exec network access blocked (enable --unsafe-mode to allow).",
                metadata={"unsafe_blocked": True},
            )

        allowed = set(args.allowed_imports) if args.allowed_imports else set(_DEFAULT_SAFE_IMPORTS)
        allowed -= _BANNED_IMPORTS
        violation = _validate_python_code(args.code, allow_network=args.allow_network, allowed_imports=allowed)
        if violation:
            return ToolResult(
                success=False,
                error=f"python_exec blocked: {violation}",
                metadata={"unsafe_blocked": True},
            )

        tmp = ctx.workspace_dir / f"python_exec_{int(time.time()*1000)}.py"
        tmp.write_text(args.code, encoding="utf-8")
        try:
            proc = subprocess.run(
                [sys.executable, "-I", str(tmp)],
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
        if not cfg.allow_human_ask:
            return ToolResult(
                success=False,
                error="human_ask disabled (set AUTO_ALLOW_HUMAN_ASK=1 to enable)",
                metadata={"needs_human": True},
            )
        answer = input(f"\n[HUMAN INPUT NEEDED]\n{args.question}\n> ").strip()
        return ToolResult(success=True, output={"answer": answer})

    return human_ask


class FinishArgs(BaseModel):
    summary: str = ""


def finish(ctx: RunContext, args: FinishArgs) -> ToolResult:
    return ToolResult(success=True, output={"summary": args.summary})


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


class ShellExecArgs(BaseModel):
    command: str
    timeout_seconds: int = 30
    cwd: Optional[str] = None


def shell_exec(ctx: RunContext, args: ShellExecArgs) -> ToolResult:
    try:
        proc = subprocess.run(
            args.command,
            cwd=args.cwd or str(ctx.workspace_dir),
            capture_output=True,
            text=True,
            timeout=args.timeout_seconds,
            shell=True,
        )
        return ToolResult(
            success=proc.returncode == 0,
            output={"exit_code": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr},
            error=None if proc.returncode == 0 else (proc.stderr.strip() or f"exit_code={proc.returncode}"),
        )
    except subprocess.TimeoutExpired:
        return ToolResult(success=False, error="shell_exec timeout", retryable=True)


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
            },
        )
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


def build_default_tool_registry(cfg: AgentConfig, run_dir: Path, *, memory_store: Optional[SqliteMemoryStore] = None) -> ToolRegistry:
    workspace_dir = run_dir / "workspace"
    workspace_dir.mkdir(parents=True, exist_ok=True)

    reg = ToolRegistry(agent_cfg=cfg)
    reg.register(ToolSpec(name="web_fetch", args_model=WebFetchArgs, fn=web_fetch, description="HTTP GET (with timeouts)"))
    reg.register(ToolSpec(name="file_read", args_model=FileReadArgs, fn=file_read, description="Read a file"))
    reg.register(
        ToolSpec(
            name="file_write",
            args_model=FileWriteArgs,
            fn=file_write_factory(cfg),
            description="Write a file (restricted to run workspace unless unsafe_mode)",
        )
    )
    reg.register(ToolSpec(name="list_dir", args_model=ListDirArgs, fn=list_dir, description="List directory entries"))
    reg.register(ToolSpec(name="glob_paths", args_model=GlobArgs, fn=glob_paths, description="Find paths by glob pattern"))
    reg.register(ToolSpec(name="file_search", args_model=FileSearchArgs, fn=file_search, description="Search text in files"))
    reg.register(
        ToolSpec(
            name="file_copy",
            args_model=FileCopyArgs,
            fn=file_copy_factory(cfg),
            description="Copy files/directories (restricted to run workspace unless unsafe_mode)",
        )
    )
    reg.register(
        ToolSpec(
            name="file_move",
            args_model=FileMoveArgs,
            fn=file_move_factory(cfg),
            description="Move files/directories (restricted to run workspace unless unsafe_mode)",
        )
    )
    reg.register(
        ToolSpec(
            name="file_delete",
            args_model=FileDeleteArgs,
            fn=file_delete_factory(cfg),
            description="Delete files/directories (restricted to run workspace unless unsafe_mode)",
        )
    )
    reg.register(
        ToolSpec(
            name="zip_extract",
            args_model=ZipExtractArgs,
            fn=zip_extract_factory(cfg),
            description="Extract zip to a directory (restricted to run workspace unless unsafe_mode)",
        )
    )
    reg.register(
        ToolSpec(
            name="zip_create",
            args_model=ZipCreateArgs,
            fn=zip_create_factory(cfg),
            description="Create zip from file/dir (restricted to run workspace unless unsafe_mode)",
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
            description="Run sandboxed Python (best-effort, network disabled unless unsafe_mode)",
        )
    )
    reg.register(
        ToolSpec(
            name="human_ask",
            args_model=HumanAskArgs,
            fn=human_ask_factory(cfg),
            description="Ask a human for help (disabled by default; set AUTO_ALLOW_HUMAN_ASK=1)",
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
    reg.register(ToolSpec(name="finish", args_model=FinishArgs, fn=finish, description="Stop successfully"))
    reg.register(
        ToolSpec(
            name="shell_exec",
            args_model=ShellExecArgs,
            fn=shell_exec,
            description="Execute a shell command (unsafe)",
            dangerous=True,
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

    if cfg.enable_web_gui:
        reg.register(
            ToolSpec(
                name="web_gui_snapshot",
                args_model=WebGuiSnapshotArgs,
                fn=web_gui_snapshot,
                description="Capture url + visible text + a11y tree (Playwright)",
            )
        )

    if cfg.enable_desktop:
        reg.register(
            ToolSpec(
                name="desktop",
                args_model=DesktopStubArgs,
                fn=desktop_action,
                description="Desktop automation via PyAutoGUI",
                dangerous=True,
            )
        )

    return reg
