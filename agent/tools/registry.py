from __future__ import annotations

"""Tool registry for resolving adapters by task type."""

from typing import Dict

from agent.schemas.task_schema import TaskType
from .api import ApiTool
from .browser import BrowserTool
from .fs import FilesystemTool
from .python_exec import PythonExecTool
from .shell import ShellTool
from .desktop import DesktopTool
from .screen_recorder import ScreenRecorderTool
from .vision import VisionTool
from .notify import NotifyTool


_REGISTRY: Dict[TaskType, object] = {
    TaskType.browser: BrowserTool(),
    TaskType.shell: ShellTool(),
    TaskType.python: PythonExecTool(),
    TaskType.fs: FilesystemTool(),
    TaskType.api: ApiTool(),
    TaskType.desktop: DesktopTool(),
    TaskType.screen_recorder: ScreenRecorderTool(),
    TaskType.vision: VisionTool(),
    TaskType.notify: NotifyTool(),
}


def get_tool(task_type: TaskType):
    if task_type not in _REGISTRY:
        raise KeyError(f"No tool registered for task type {task_type}")
    return _REGISTRY[task_type]
