from __future__ import annotations

import json
import logging
import os
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IntegrationSpec:
    key: str
    label: str
    kind: str
    mcp_servers: Tuple[str, ...] = ()
    local_tools: Tuple[str, ...] = ()


_INTEGRATIONS: List[IntegrationSpec] = [
    IntegrationSpec(
        key="google_calendar",
        label="Google Calendar",
        kind="calendar",
        mcp_servers=("google-calendar",),
        local_tools=(
            "list_calendar_events",
            "get_free_time",
            "check_calendar_conflicts",
            "create_calendar_event",
            "update_calendar_event",
            "delete_calendar_event",
            "calendar_list_events",
            "calendar_create_event",
            "calendar_update_event",
            "calendar_delete_event",
            "calendar_find_free_slots",
        ),
    ),
    IntegrationSpec(
        key="google_tasks",
        label="Google Tasks",
        kind="tasks",
        mcp_servers=("google-tasks",),
        local_tools=(
            "list_task_lists",
            "list_all_tasks",
            "create_task",
            "complete_task",
            "search_tasks",
            "update_task",
            "delete_task",
            "get_task_details",
        ),
    ),
    IntegrationSpec(
        key="yahoo_imap",
        label="Yahoo IMAP",
        kind="email",
        local_tools=("mail",),
    ),
    IntegrationSpec(
        key="blackboard",
        label="Blackboard",
        kind="education",
        local_tools=("blackboard_snapshot",),
    ),
    IntegrationSpec(
        key="coachrx",
        label="CoachRX",
        kind="training",
        local_tools=("coachrx_snapshot",),
    ),
    IntegrationSpec(
        key="obsidian",
        label="Obsidian",
        kind="notes",
        mcp_servers=("obsidian",),
    ),
    IntegrationSpec(
        key="github",
        label="GitHub",
        kind="code",
        mcp_servers=("github",),
    ),
    IntegrationSpec(
        key="filesystem_mcp",
        label="Filesystem MCP",
        kind="filesystem",
        mcp_servers=("filesystem",),
    ),
]

_INTEGRATION_BY_KEY = {spec.key: spec for spec in _INTEGRATIONS}
_MCP_SERVER_TO_INTEGRATION = {
    server: spec.key
    for spec in _INTEGRATIONS
    for server in spec.mcp_servers
}
_LOCAL_TOOL_TO_INTEGRATION = {
    tool: spec.key
    for spec in _INTEGRATIONS
    for tool in spec.local_tools
}


@dataclass
class IntegrationSettings:
    enabled: Dict[str, bool] = field(default_factory=dict)
    auto_enable_on_use: bool = True


class IntegrationManager:
    def __init__(self, settings_path: Optional[Path] = None) -> None:
        self._lock = threading.Lock()
        self._settings_path = (
            settings_path
            if settings_path is not None
            else Path.home() / ".drcodept_swarm" / "integrations.json"
        )
        self._settings = self._load_settings()

    @property
    def settings_path(self) -> Path:
        return self._settings_path

    def _load_settings(self) -> IntegrationSettings:
        defaults = {spec.key: True for spec in _INTEGRATIONS}
        if not self._settings_path.exists():
            return IntegrationSettings(enabled=defaults, auto_enable_on_use=True)
        try:
            data = json.loads(self._settings_path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning(f"Failed to read integrations config: {exc}")
            return IntegrationSettings(enabled=defaults, auto_enable_on_use=True)
        enabled = dict(defaults)
        raw_enabled = data.get("enabled") if isinstance(data, dict) else None
        if isinstance(raw_enabled, dict):
            for key, value in raw_enabled.items():
                if key in enabled:
                    enabled[key] = bool(value)
        auto_enable = True
        if isinstance(data, dict) and "auto_enable_on_use" in data:
            auto_enable = bool(data.get("auto_enable_on_use"))
        return IntegrationSettings(enabled=enabled, auto_enable_on_use=auto_enable)

    def save(self) -> None:
        with self._lock:
            self._settings_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "enabled": dict(self._settings.enabled),
                "auto_enable_on_use": bool(self._settings.auto_enable_on_use),
            }
            self._settings_path.write_text(
                json.dumps(payload, indent=2), encoding="utf-8"
            )

    def list_integrations(self) -> List[IntegrationSpec]:
        return list(_INTEGRATIONS)

    def is_enabled(self, key: str) -> bool:
        return bool(self._settings.enabled.get(key, True))

    def set_enabled(self, key: str, enabled: bool, *, reason: str = "") -> bool:
        if key not in _INTEGRATION_BY_KEY:
            return False
        with self._lock:
            previous = self._settings.enabled.get(key, True)
            if previous == enabled:
                return False
            self._settings.enabled[key] = enabled
            self.save()
        if reason:
            logger.info(f"Integration {key} set to {enabled}: {reason}")
        return True

    def toggle(self, key: str) -> bool:
        return self.set_enabled(key, not self.is_enabled(key))

    def enable_all(self) -> None:
        with self._lock:
            for spec in _INTEGRATIONS:
                self._settings.enabled[spec.key] = True
            self.save()

    def disable_all(self) -> None:
        with self._lock:
            for spec in _INTEGRATIONS:
                self._settings.enabled[spec.key] = False
            self.save()

    def auto_enable_on_use(self) -> bool:
        return bool(self._settings.auto_enable_on_use)

    def set_auto_enable_on_use(self, enabled: bool) -> None:
        with self._lock:
            if self._settings.auto_enable_on_use == enabled:
                return
            self._settings.auto_enable_on_use = enabled
            self.save()

    def integration_for_tool(self, tool_name: str) -> Optional[str]:
        if not tool_name:
            return None
        if "." in tool_name:
            server = tool_name.split(".", 1)[0]
            return _MCP_SERVER_TO_INTEGRATION.get(server)
        return _LOCAL_TOOL_TO_INTEGRATION.get(tool_name)

    def should_expose_tool(self, tool_name: str) -> bool:
        integration = self.integration_for_tool(tool_name)
        if not integration:
            return True
        if self.is_enabled(integration):
            return True
        return self.auto_enable_on_use()

    def ensure_enabled_for_tool(self, tool_name: str, *, reason: str = "") -> Tuple[bool, bool]:
        integration = self.integration_for_tool(tool_name)
        if not integration:
            return True, False
        if self.is_enabled(integration):
            return True, False
        if self.auto_enable_on_use():
            self.set_enabled(integration, True, reason=reason or f"auto-enable for {tool_name}")
            return True, True
        return False, False

    def should_load_mcp(self) -> bool:
        if os.getenv("TREYS_AGENT_DISABLE_MCP"):
            return False
        if self.auto_enable_on_use():
            return True
        for spec in _INTEGRATIONS:
            if spec.mcp_servers and self.is_enabled(spec.key):
                return True
        return False

    def enabled_integrations(self) -> Dict[str, bool]:
        return dict(self._settings.enabled)


_MANAGER: Optional[IntegrationManager] = None


def get_integration_manager() -> IntegrationManager:
    global _MANAGER
    if _MANAGER is None:
        _MANAGER = IntegrationManager()
    return _MANAGER
