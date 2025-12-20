from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from agent.llm.codex_cli_client import CodexCliClient
from agent.llm.errors import CodexCliExecutionError, CodexCliNotFoundError, CodexCliOutputError


def _write_schema(tmp_path: Path) -> Path:
    schema = tmp_path / "schema.json"
    schema.write_text('{"type":"object"}', encoding="utf-8")
    return schema


def test_codex_cli_nonzero_exit_is_surfaced(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    schema = _write_schema(tmp_path)

    monkeypatch.setattr(shutil, "which", lambda _: "codex")

    def fake_run(cmd, capture_output, text, timeout):  # noqa: ARG001
        return subprocess.CompletedProcess(cmd, 7, stdout="oops", stderr="bad")

    monkeypatch.setattr(subprocess, "run", fake_run)

    client = CodexCliClient(codex_bin="codex")
    with pytest.raises(CodexCliExecutionError) as exc:
        client.complete_json("hello", schema_path=schema)
    assert "exit=7" in str(exc.value)


def test_codex_cli_invalid_json_is_surfaced(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    schema = _write_schema(tmp_path)

    monkeypatch.setattr(shutil, "which", lambda _: "codex")

    def fake_run(cmd, capture_output, text, timeout):  # noqa: ARG001
        out_path = cmd[cmd.index("--output-last-message") + 1]
        Path(out_path).write_text("NOT JSON", encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    client = CodexCliClient(codex_bin="codex")
    with pytest.raises(CodexCliOutputError):
        client.complete_json("hello", schema_path=schema)


def test_codex_cli_parses_valid_json(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    schema = _write_schema(tmp_path)

    monkeypatch.setattr(shutil, "which", lambda _: "codex")

    captured = {}

    def fake_run(cmd, capture_output, text, timeout):  # noqa: ARG001
        captured["cmd"] = cmd
        out_path = cmd[cmd.index("--output-last-message") + 1]
        Path(out_path).write_text('{"ok": true}', encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    client = CodexCliClient(codex_bin="codex")
    out = client.complete_json("hello", schema_path=schema)
    assert out == {"ok": True}

    # Ensure required flags are present
    cmd = captured["cmd"]
    assert cmd[0] == "codex"
    assert "exec" in cmd
    assert "--dangerously-bypass-approvals-and-sandbox" in cmd
    assert "--search" in cmd
    assert "--output-schema" in cmd
    assert "--output-last-message" in cmd
    assert cmd.index("--dangerously-bypass-approvals-and-sandbox") < cmd.index("exec")
    assert cmd.index("--search") < cmd.index("exec")


def test_codex_cli_missing_binary_raises_clear_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    schema = _write_schema(tmp_path)
    monkeypatch.setattr(shutil, "which", lambda _: None)
    client = CodexCliClient(codex_bin="codex")
    with pytest.raises(CodexCliNotFoundError):
        client.complete_json("hello", schema_path=schema)
