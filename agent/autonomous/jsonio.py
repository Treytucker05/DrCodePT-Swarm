from __future__ import annotations

import json
from typing import Any, Optional, Type, TypeVar

from pydantic import BaseModel, ValidationError

from .pydantic_compat import model_validate


class JsonParseError(ValueError):
    pass


ModelT = TypeVar("ModelT", bound=BaseModel)


def parse_json(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise JsonParseError(str(exc))


def parse_model(model_cls: Type[ModelT], text: str) -> ModelT:
    data = parse_json(text)
    try:
        return model_validate(model_cls, data)
    except ValidationError as exc:
        raise JsonParseError(str(exc))


def dumps_compact(obj: Any, *, max_chars: int = 18_000) -> str:
    s = json.dumps(obj, ensure_ascii=False, sort_keys=True, default=str)
    if len(s) <= max_chars:
        return s
    return s[:max_chars] + "…"

