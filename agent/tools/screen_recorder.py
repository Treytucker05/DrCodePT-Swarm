from __future__ import annotations

"""
Screen recording tool using FFmpeg (gdigrab on Windows).
Actions:
- start_recording: action="start", output_path optional
- stop_recording: action="stop"
"""

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict

from .base import ToolAdapter, ToolResult


def _ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


class ScreenRecorderTool(ToolAdapter):
    tool_name = "screen_recorder"

    def __init__(self):
        self.process: subprocess.Popen | None = None
        self.output_path: Path | None = None

    def _build_command(self, output: Path, framerate: int = 30):
        # gdigrab works for full desktop on Windows
        return [
            "ffmpeg",
            "-y",
            "-f",
            "gdigrab",
            "-framerate",
            str(framerate),
            "-i",
            "desktop",
            "-vcodec",
            "libx264",
            "-preset",
            "ultrafast",
            "-pix_fmt",
            "yuv420p",
            str(output),
        ]

    def execute(self, task, inputs: Dict[str, Any]) -> ToolResult:
        action = inputs.get("action") or getattr(task, "action", None)
        if not action:
            return ToolResult(False, error="No action provided for screen recorder")

        if action == "start":
            if self.process and self.process.poll() is None:
                return ToolResult(False, error="Recording already in progress")
            if not _ffmpeg_available():
                return ToolResult(False, error="ffmpeg not found. Install with: winget install ffmpeg")

            output_path = inputs.get("output_path")
            if output_path:
                out = Path(output_path)
            else:
                out = Path(tempfile.gettempdir()) / "screen_recording.mp4"
            out.parent.mkdir(parents=True, exist_ok=True)
            cmd = self._build_command(out, framerate=int(inputs.get("framerate", 30)))
            try:
                creationflags = 0x08000000 if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
                self.process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=creationflags,
                )
                self.output_path = out
                return ToolResult(True, output={"recording": str(out)})
            except FileNotFoundError:
                return ToolResult(False, error="ffmpeg executable not found in PATH")
            except Exception as exc:  # pragma: no cover
                return ToolResult(False, error=str(exc))

        if action == "stop":
            if not self.process or self.process.poll() is not None:
                return ToolResult(False, error="No active recording to stop")
            try:
                # Signal ffmpeg to stop cleanly
                if self.process.stdin:
                    self.process.stdin.write(b"q")
                    self.process.stdin.flush()
                self.process.wait(timeout=5)
            except Exception:
                self.process.kill()
            finally:
                self.process = None
            return ToolResult(True, output={"video_path": str(self.output_path) if self.output_path else None})

        return ToolResult(False, error=f"Unsupported screen recorder action '{action}'")
