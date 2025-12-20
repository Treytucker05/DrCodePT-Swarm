from __future__ import annotations

from typing import Any, Dict, Optional, Type

from .base import VerifierAdapter


_REGISTRY: Dict[str, Type[VerifierAdapter]] = {}


def _register(cls: Type[VerifierAdapter]) -> None:
    if not getattr(cls, "verifier_id", None):
        raise ValueError("VerifierAdapter.verifier_id is required")
    _REGISTRY[cls.verifier_id] = cls


def _init_defaults() -> None:
    if _REGISTRY:
        return

    from .api_status_ok import ApiStatusOkVerifier
    from .command_exit_zero import CommandExitZeroVerifier
    from .file_exists import FileExistsVerifier
    from .json_has_entries import JsonHasEntriesVerifier
    from .page_contains import PageContainsVerifier
    from .text_in_file import TextInFileVerifier

    for cls in (
        FileExistsVerifier,
        TextInFileVerifier,
        PageContainsVerifier,
        CommandExitZeroVerifier,
        ApiStatusOkVerifier,
        JsonHasEntriesVerifier,
    ):
        _register(cls)


def get_verifier(verifier_id: str, args: Optional[Dict[str, Any]] = None) -> VerifierAdapter:
    _init_defaults()
    cls = _REGISTRY.get(verifier_id)
    if cls is None:
        raise KeyError(f"Unknown verifier: {verifier_id}")
    return cls(args=args)


def list_verifiers() -> Dict[str, Type[VerifierAdapter]]:
    _init_defaults()
    return dict(_REGISTRY)


__all__ = ["get_verifier", "list_verifiers"]
