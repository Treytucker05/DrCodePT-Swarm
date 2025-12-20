from __future__ import annotations

import ast
import json
import subprocess
import sys
import time
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

        if not agent_cfg.unsafe_mode and not _is_within(path, ctx.workspace_dir):
            return ToolResult(
                success=False,
                error=f"Write blocked outside workspace: {path}",
                metadata={"unsafe_blocked": True, "workspace_dir": str(ctx.workspace_dir)},
            )

        path.parent.mkdir(parents=True, exist_ok=True)
        if args.mode == "append":
            with path.open("a", encoding="utf-8", errors="replace", newline="\n") as f:
                f.write(args.content)
        else:
            path.write_text(args.content, encoding="utf-8", errors="replace")
        return ToolResult(success=True, output={"path": str(path), "bytes": len(args.content.encode("utf-8"))})

    return file_write


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


def human_ask(ctx: RunContext, args: HumanAskArgs) -> ToolResult:
    answer = input(f"\n[HUMAN INPUT NEEDED]\n{args.question}\n> ").strip()
    return ToolResult(success=True, output={"answer": answer})


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


def desktop_stub(ctx: RunContext, args: DesktopStubArgs) -> ToolResult:
    return ToolResult(success=False, error="Desktop adapter not implemented in v1 (stub).")


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
    reg.register(
        ToolSpec(
            name="python_exec",
            args_model=PythonExecArgs,
            fn=python_exec_factory(cfg),
            description="Run sandboxed Python (best-effort, network disabled unless unsafe_mode)",
        )
    )
    reg.register(ToolSpec(name="human_ask", args_model=HumanAskArgs, fn=human_ask, description="Ask a human for help"))
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
                name="desktop_stub",
                args_model=DesktopStubArgs,
                fn=desktop_stub,
                description="Desktop automation adapter stub (v1 placeholder)",
            )
        )

    return reg
