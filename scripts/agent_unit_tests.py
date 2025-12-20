from __future__ import annotations

import json
import tempfile
import sys
from pathlib import Path
from typing import Any, Dict, List

from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.autonomous.config import AgentConfig, PlannerConfig, RunnerConfig, RunContext
from agent.autonomous.llm.stub import StubLLM
from agent.autonomous.memory.sqlite_store import SqliteMemoryStore
from agent.autonomous.models import ToolResult
from agent.autonomous.runner import AgentRunner
from agent.autonomous.tools.registry import ToolRegistry, ToolSpec


class EmptyArgs(BaseModel):
    pass


class FakeArgs(BaseModel):
    payload: str = ""


class UrlArgs(BaseModel):
    url: str
    include_screenshot: bool = True


class HumanAskArgs(BaseModel):
    question: str


def _finish(ctx: RunContext, args: EmptyArgs) -> ToolResult:
    return ToolResult(success=True, output={"summary": "done"})


def _make_registry(agent_cfg: AgentConfig, specs: List[ToolSpec]) -> ToolRegistry:
    registry = ToolRegistry(agent_cfg)
    for spec in specs:
        registry.register(spec)
    registry.register(ToolSpec(name="finish", args_model=EmptyArgs, fn=_finish))
    return registry


def _read_trace(path: Path) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    if not path.is_file():
        return events
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            events.append(json.loads(line))
        except Exception:
            continue
    return events


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_preconditions_block() -> None:
    calls = {"fake": 0}

    def fake_tool(ctx: RunContext, args: FakeArgs) -> ToolResult:
        calls["fake"] += 1
        return ToolResult(success=True, output={"ok": True})

    agent_cfg = AgentConfig()
    registry = _make_registry(
        agent_cfg,
        [
            ToolSpec(name="fake_tool", args_model=FakeArgs, fn=fake_tool),
        ],
    )
    responses = [
        {
            "goal": "test",
            "steps": [
                {
                    "goal": "do fake",
                    "tool_name": "fake_tool",
                    "tool_args": {"payload": "x"},
                    "success_criteria": ["should not run"],
                    "preconditions": ["must have foo"],
                }
            ],
        },
        {
            "ok": False,
            "failed": [
                {"condition": "must have foo", "reason": "missing"},
                {"condition": "must have bar", "reason": "missing"},
                {"condition": "must have baz", "reason": "missing"},
            ],
        },
        {"status": "replan", "explanation_short": "precondition failed", "next_hint": ""},
        {
            "goal": "finish",
            "steps": [
                {
                    "goal": "finish",
                    "tool_name": "finish",
                    "tool_args": {},
                    "success_criteria": ["done"],
                }
            ],
        },
        {"status": "success", "explanation_short": "done", "next_hint": ""},
    ]
    with tempfile.TemporaryDirectory() as tmp:
        run_dir = Path(tmp) / "run"
        run_dir.mkdir(parents=True, exist_ok=True)
        runner = AgentRunner(
            cfg=RunnerConfig(max_steps=4, timeout_seconds=30),
            agent_cfg=agent_cfg,
            planner_cfg=PlannerConfig(mode="react"),
            llm=StubLLM(responses=responses),
            run_dir=run_dir,
            tools=registry,
        )
        result = runner.run(task="test preconditions")
        _assert(result.success, "run should finish successfully")
        _assert(calls["fake"] == 0, "fake tool should not execute when preconditions fail")
        events = _read_trace(Path(result.trace_path))
        cond = [e for e in events if e.get("type") == "condition_check" and e.get("kind") == "preconditions"]
        _assert(cond, "preconditions condition_check event missing")
        report = cond[0].get("report") or {}
        _assert(report.get("ok") is False, "preconditions report should be ok=false")


def test_postconditions_trigger_replan() -> None:
    calls = {"fake": 0}

    def fake_tool(ctx: RunContext, args: FakeArgs) -> ToolResult:
        calls["fake"] += 1
        return ToolResult(success=True, output={"ok": True})

    agent_cfg = AgentConfig()
    registry = _make_registry(
        agent_cfg,
        [
            ToolSpec(name="fake_tool", args_model=FakeArgs, fn=fake_tool),
        ],
    )
    responses = [
        {
            "goal": "test",
            "steps": [
                {
                    "goal": "do fake",
                    "tool_name": "fake_tool",
                    "tool_args": {"payload": "x"},
                    "success_criteria": ["run"],
                    "postconditions": ["a", "b", "c"],
                }
            ],
        },
        {
            "ok": False,
            "failed": [
                {"condition": "a", "reason": "missing"},
                {"condition": "b", "reason": "missing"},
                {"condition": "c", "reason": "missing"},
            ],
        },
        {"status": "success", "explanation_short": "tool ran", "next_hint": ""},
        {
            "goal": "finish",
            "steps": [
                {
                    "goal": "finish",
                    "tool_name": "finish",
                    "tool_args": {},
                    "success_criteria": ["done"],
                }
            ],
        },
        {"status": "success", "explanation_short": "done", "next_hint": ""},
    ]
    with tempfile.TemporaryDirectory() as tmp:
        run_dir = Path(tmp) / "run"
        run_dir.mkdir(parents=True, exist_ok=True)
        runner = AgentRunner(
            cfg=RunnerConfig(max_steps=4, timeout_seconds=30),
            agent_cfg=agent_cfg,
            planner_cfg=PlannerConfig(mode="react"),
            llm=StubLLM(responses=responses),
            run_dir=run_dir,
            tools=registry,
        )
        result = runner.run(task="test postconditions")
        _assert(result.success, "run should finish successfully")
        _assert(calls["fake"] == 1, "fake tool should execute once")
        events = _read_trace(Path(result.trace_path))
        step_events = [e for e in events if e.get("type") == "step"]
        _assert(step_events, "step event missing")
        first_reflection = step_events[0].get("reflection") or {}
        _assert(first_reflection.get("status") == "replan", "postconditions failure should force replan")


def test_memory_write_persisted() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        run_dir = Path(tmp) / "run"
        run_dir.mkdir(parents=True, exist_ok=True)
        mem_path = run_dir / "memory.sqlite3"
        agent_cfg = AgentConfig(memory_db_path=mem_path)
        registry = _make_registry(agent_cfg, [])
        responses = [
            {
                "goal": "test",
                "steps": [
                    {
                        "goal": "finish",
                        "tool_name": "finish",
                        "tool_args": {},
                        "success_criteria": ["done"],
                    }
                ],
            },
            {
                "status": "success",
                "explanation_short": "done",
                "next_hint": "",
                "memory_write": {"kind": "knowledge", "content": "remember this", "key": "k1"},
            },
        ]
        runner = AgentRunner(
            cfg=RunnerConfig(max_steps=2, timeout_seconds=30),
            agent_cfg=agent_cfg,
            planner_cfg=PlannerConfig(mode="react"),
            llm=StubLLM(responses=responses),
            run_dir=run_dir,
            tools=registry,
        )
        result = runner.run(task="test memory")
        _assert(result.success, "run should finish successfully")
        store = SqliteMemoryStore(mem_path)
        records = store.search("remember", limit=5)
        _assert(records, "memory record not stored")
        store.close()
        events = _read_trace(Path(result.trace_path))
        mem_events = [e for e in events if e.get("type") == "memory_write" and e.get("status") == "stored"]
        _assert(mem_events, "memory_write event not logged")


def test_ui_snapshot_in_planning_context() -> None:
    calls = {"web": 0, "snapshot": 0}

    def web_fail(ctx: RunContext, args: UrlArgs) -> ToolResult:
        calls["web"] += 1
        return ToolResult(success=False, error="web failed")

    def web_gui_snapshot(ctx: RunContext, args: UrlArgs) -> ToolResult:
        calls["snapshot"] += 1
        return ToolResult(
            success=True,
            output={"url": args.url, "screenshot": str(ctx.run_dir / "snap.png"), "a11y": {}},
        )

    agent_cfg = AgentConfig()
    registry = _make_registry(
        agent_cfg,
        [
            ToolSpec(name="web_fail", args_model=UrlArgs, fn=web_fail),
            ToolSpec(name="web_gui_snapshot", args_model=UrlArgs, fn=web_gui_snapshot),
        ],
    )
    responses = [
        {
            "goal": "test",
            "steps": [
                {
                    "goal": "visit",
                    "tool_name": "web_fail",
                    "tool_args": {"url": "https://example.com"},
                    "success_criteria": ["should fail"],
                }
            ],
        },
        {"status": "replan", "explanation_short": "failed", "next_hint": ""},
        {
            "goal": "finish",
            "steps": [
                {
                    "goal": "finish",
                    "tool_name": "finish",
                    "tool_args": {},
                    "success_criteria": ["done"],
                }
            ],
        },
        {"status": "success", "explanation_short": "done", "next_hint": ""},
    ]
    llm = StubLLM(responses=responses)
    with tempfile.TemporaryDirectory() as tmp:
        run_dir = Path(tmp) / "run"
        run_dir.mkdir(parents=True, exist_ok=True)
        runner = AgentRunner(
            cfg=RunnerConfig(max_steps=3, timeout_seconds=30),
            agent_cfg=agent_cfg,
            planner_cfg=PlannerConfig(mode="react"),
            llm=llm,
            run_dir=run_dir,
            tools=registry,
        )
        result = runner.run(task="test ui snapshot")
        _assert(result.success, "run should finish successfully")
        _assert(calls["snapshot"] == 1, "web_gui_snapshot should be called once")
        events = _read_trace(Path(result.trace_path))
        snapshot_events = [e for e in events if e.get("type") == "ui_snapshot"]
        _assert(snapshot_events, "ui_snapshot event missing")
        prompt_contains_snapshot = any("ui_snapshot" in prompt for prompt in llm.calls)
        _assert(prompt_contains_snapshot, "ui_snapshot not included in planning prompt")


def test_approval_required_replan() -> None:
    calls = {"danger": 0}

    def danger_tool(ctx: RunContext, args: EmptyArgs) -> ToolResult:
        calls["danger"] += 1
        return ToolResult(success=True, output={"ok": True})

    def human_ask(ctx: RunContext, args: HumanAskArgs) -> ToolResult:
        return ToolResult(success=True, output={"answer": "no"})

    agent_cfg = AgentConfig(allow_human_ask=True)
    registry = _make_registry(
        agent_cfg,
        [
            ToolSpec(name="danger_tool", args_model=EmptyArgs, fn=danger_tool, approval_required=True),
            ToolSpec(name="human_ask", args_model=HumanAskArgs, fn=human_ask),
        ],
    )
    responses = [
        {
            "goal": "test",
            "steps": [
                {
                    "goal": "danger",
                    "tool_name": "danger_tool",
                    "tool_args": {},
                    "success_criteria": ["blocked"],
                }
            ],
        },
        {"status": "success", "explanation_short": "blocked", "next_hint": ""},
        {
            "goal": "finish",
            "steps": [
                {
                    "goal": "finish",
                    "tool_name": "finish",
                    "tool_args": {},
                    "success_criteria": ["done"],
                }
            ],
        },
        {"status": "success", "explanation_short": "done", "next_hint": ""},
    ]
    with tempfile.TemporaryDirectory() as tmp:
        run_dir = Path(tmp) / "run"
        run_dir.mkdir(parents=True, exist_ok=True)
        runner = AgentRunner(
            cfg=RunnerConfig(max_steps=3, timeout_seconds=30),
            agent_cfg=agent_cfg,
            planner_cfg=PlannerConfig(mode="react"),
            llm=StubLLM(responses=responses),
            run_dir=run_dir,
            tools=registry,
        )
        result = runner.run(task="test approval")
        _assert(result.success, "run should finish successfully")
        _assert(calls["danger"] == 0, "danger tool should not execute without approval")
        events = _read_trace(Path(result.trace_path))
        error_reports = [e for e in events if e.get("type") == "error_report" and e.get("reason") == "approval_required"]
        _assert(error_reports, "approval error_report missing")


def main() -> int:
    tests = [
        ("preconditions_block", test_preconditions_block),
        ("postconditions_trigger_replan", test_postconditions_trigger_replan),
        ("memory_write_persisted", test_memory_write_persisted),
        ("ui_snapshot_in_planning_context", test_ui_snapshot_in_planning_context),
        ("approval_required_replan", test_approval_required_replan),
    ]
    results: List[Dict[str, Any]] = []
    failed = 0
    for name, fn in tests:
        try:
            fn()
            results.append({"test_name": name, "outcome": "pass", "details": None})
        except Exception as exc:
            failed += 1
            results.append({"test_name": name, "outcome": "fail", "details": str(exc)})
    print(json.dumps(results, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
