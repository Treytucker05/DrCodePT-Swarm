from __future__ import annotations

import json
from typing import Any, Dict, Iterable


def _coerce_json_value(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    text = value.strip()
    if not text:
        return value
    if text[0] in "{[\"-" or text.isdigit() or text in {"true", "false", "null"}:
        try:
            return json.loads(text)
        except Exception:
            return value
    return value


def _kv_list_to_dict(items: Iterable[Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        key = item.get("key")
        if key is None:
            continue
        value = item.get("value")
        out[str(key)] = _coerce_json_value(value)
    return out


def coerce_plan_dict(data: Any) -> Any:
    if not isinstance(data, dict):
        return data
    steps = data.get("steps")
    if not isinstance(steps, list):
        return data
    for step in steps:
        if not isinstance(step, dict):
            continue
        tool_args = step.get("tool_args")
        if tool_args is None:
            step["tool_args"] = {}
        elif isinstance(tool_args, list):
            step["tool_args"] = _kv_list_to_dict(tool_args)
        elif not isinstance(tool_args, dict):
            step["tool_args"] = {}
    return data


def coerce_plan_candidates_dict(data: Any) -> Any:
    if not isinstance(data, dict):
        return data
    plans = data.get("plans")
    if not isinstance(plans, list):
        return data
    for item in plans:
        if not isinstance(item, dict):
            continue
        plan = item.get("plan")
        if isinstance(plan, dict):
            coerce_plan_dict(plan)
    return data

