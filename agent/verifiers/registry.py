from __future__ import annotations

"""Verifier registry."""

from typing import Dict

from .api_status_ok import ApiStatusOkVerifier
from .base import Verifier
from .command_exit_zero import CommandExitZeroVerifier
from .file_exists import FileExistsVerifier
from .json_has_entries import JsonHasEntriesVerifier
from .page_contains import PageContainsVerifier
from .text_in_file import TextInFileVerifier


_REGISTRY: Dict[str, type[Verifier]] = {
    "file_exists": FileExistsVerifier,
    "json_has_entries": JsonHasEntriesVerifier,
    "text_in_file": TextInFileVerifier,
    "page_contains": PageContainsVerifier,
    "command_exit_zero": CommandExitZeroVerifier,
    "api_status_ok": ApiStatusOkVerifier,
}


def get_verifier(vid: str, args: dict) -> Verifier:
    if vid not in _REGISTRY:
        raise KeyError(f"Verifier '{vid}' not found")
    return _REGISTRY[vid](args)

