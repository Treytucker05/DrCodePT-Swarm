from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .registry import McpServerSpec


@dataclass
class McpResponse:
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


class MCPClient:
    def __init__(self, server: McpServerSpec, *, timeout_seconds: int = 15) -> None:
        self.server = server
        self.timeout_seconds = max(5, int(timeout_seconds))
        self._id = 0

    def _spawn(self) -> subprocess.Popen:
        env = os.environ.copy()
        env.update(self.server.env)
        return subprocess.Popen(
            [self.server.command, *self.server.args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )

    def _send(self, proc: subprocess.Popen, method: str, params: Optional[Dict[str, Any]] = None) -> McpResponse:
        self._id += 1
        payload = {"jsonrpc": "2.0", "id": self._id, "method": method}
        if params is not None:
            payload["params"] = params
        msg = json.dumps(payload, ensure_ascii=False)
        assert proc.stdin is not None
        proc.stdin.write(msg + "\n")
        proc.stdin.flush()
        return self._read(proc, self._id)

    def _notify(self, proc: subprocess.Popen, method: str, params: Optional[Dict[str, Any]] = None) -> None:
        payload = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        msg = json.dumps(payload, ensure_ascii=False)
        assert proc.stdin is not None
        proc.stdin.write(msg + "\n")
        proc.stdin.flush()

    def _read(self, proc: subprocess.Popen, msg_id: int) -> McpResponse:
        assert proc.stdout is not None
        start = time.monotonic()
        while time.monotonic() - start < self.timeout_seconds:
            line = proc.stdout.readline()
            if not line:
                if proc.poll() is not None:
                    break
                time.sleep(0.05)
                continue
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except Exception:
                continue
            if isinstance(data, dict) and data.get("id") == msg_id:
                return McpResponse(result=data.get("result"), error=data.get("error"))
        return McpResponse(error={"message": "timeout"})

    def _initialize(self, proc: subprocess.Popen) -> None:
        self._send(
            proc,
            "initialize",
            {
                "clientInfo": {"name": "treys-agent", "version": "1.0"},
                "capabilities": {},
            },
        )
        # Notify initialized (best effort)
        try:
            self._notify(proc, "initialized", {})
        except Exception:
            pass

    def list_tools(self) -> McpResponse:
        proc = self._spawn()
        try:
            self._initialize(proc)
            return self._send(proc, "tools/list")
        finally:
            try:
                proc.kill()
            except Exception:
                pass

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> McpResponse:
        proc = self._spawn()
        try:
            self._initialize(proc)
            return self._send(proc, "tools/call", {"name": name, "arguments": arguments})
        finally:
            try:
                proc.kill()
            except Exception:
                pass
