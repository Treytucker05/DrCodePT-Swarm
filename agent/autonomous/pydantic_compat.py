from __future__ import annotations

from typing import Any, TypeVar


ModelT = TypeVar("ModelT")


def model_validate(model_cls: type[ModelT], data: Any) -> ModelT:
    # pydantic v2: model_validate; v1: parse_obj
    if hasattr(model_cls, "model_validate"):
        return model_cls.model_validate(data)  # type: ignore[attr-defined]
    return model_cls.parse_obj(data)  # type: ignore[attr-defined]


def model_dump(model: Any) -> dict:
    # pydantic v2: model_dump; v1: dict
    if hasattr(model, "model_dump"):
        return model.model_dump()  # type: ignore[attr-defined]
    return model.dict()  # type: ignore[attr-defined]

