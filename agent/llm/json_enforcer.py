from __future__ import annotations

import json
from typing import Any, Callable, Dict, Optional, Tuple, Type

try:
    from pydantic import BaseModel
except Exception:  # pragma: no cover - pydantic import guard
    BaseModel = object  # type: ignore[assignment]


def _model_schema(model_cls: Type[BaseModel]) -> Dict[str, Any]:
    if hasattr(model_cls, "model_json_schema"):
        return model_cls.model_json_schema()  # type: ignore[attr-defined]
    if hasattr(model_cls, "schema"):
        return model_cls.schema()  # type: ignore[attr-defined]
    return {}


def _model_validate(model_cls: Type[BaseModel], data: Any) -> BaseModel:
    if hasattr(model_cls, "model_validate"):
        return model_cls.model_validate(data)  # type: ignore[attr-defined]
    return model_cls.parse_obj(data)  # type: ignore[attr-defined]


def _model_dump(model: BaseModel) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()  # type: ignore[attr-defined]
    return model.dict()  # type: ignore[attr-defined]


def extract_json(text: str) -> str:
    if not text:
        raise ValueError("Empty response")

    candidate = text.strip()

    if "```" in candidate:
        parts = candidate.split("```")
        for chunk in parts:
            chunk = chunk.strip()
            if chunk.startswith("json"):
                chunk = chunk[4:].strip()
            if chunk.startswith("{") and chunk.endswith("}"):
                return chunk
        if len(parts) >= 2:
            maybe = parts[1].strip()
            if maybe.startswith("json"):
                maybe = maybe[4:].strip()
            if maybe.startswith("{") and maybe.endswith("}"):
                return maybe

    if "{" in candidate and "}" in candidate:
        start = candidate.find("{")
        end = candidate.rfind("}") + 1
        if start >= 0 and end > start:
            return candidate[start:end]

    raise ValueError("No JSON found")


def parse_json(text: str) -> Any:
    json_str = extract_json(text)
    return json.loads(json_str)


def build_repair_prompt(schema: Dict[str, Any], previous: Optional[str] = None) -> str:
    prompt = (
        "Return ONLY valid JSON matching this schema. No prose.\n"
        "Schema:\n"
        f"{json.dumps(schema, indent=2)}\n"
    )
    if previous:
        clipped = previous.strip()
        if len(clipped) > 1200:
            clipped = clipped[:1200]
        prompt += f"Previous response (invalid):\n{clipped}\n"
    return prompt


def enforce_json_response(
    response: str,
    *,
    model_cls: Type[BaseModel],
    schema: Optional[Dict[str, Any]] = None,
    retry_call: Optional[Callable[[str], Optional[str]]] = None,
    max_retries: int = 2,
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    last_error: Optional[str] = None
    current = response
    schema = schema or _model_schema(model_cls)

    for attempt in range(max_retries + 1):
        try:
            data = parse_json(current)
            validated = _model_validate(model_cls, data)
            return _model_dump(validated), None
        except Exception as exc:
            last_error = str(exc)
            if retry_call is None or attempt >= max_retries:
                break
            repair_prompt = build_repair_prompt(schema, previous=current)
            current = retry_call(repair_prompt) or ""

    return None, last_error


__all__ = [
    "build_repair_prompt",
    "enforce_json_response",
    "extract_json",
    "parse_json",
]
