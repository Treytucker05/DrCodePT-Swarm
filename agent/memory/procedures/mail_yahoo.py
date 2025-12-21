from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


def _repo_root() -> Path:
    # file: agent/memory/procedures/mail_yahoo.py -> parents[3] == repo root
    return Path(__file__).resolve().parents[3]


def procedure_path() -> Path:
    return _repo_root() / "agent" / "memory" / "procedures" / "mail_yahoo_folders.json"


class MoveRule(BaseModel):
    name: str
    to_folder: str

    # simple matching (v0.1)
    from_contains: List[str] = Field(default_factory=list)
    subject_contains: List[str] = Field(default_factory=list)

    # safety knobs (v0.1)
    max_messages: int = 50
    newer_than_days: Optional[int] = None
    unread_only: bool = False


class MailProcedure(BaseModel):
    version: str = "0.1"
    provider: Literal["yahoo"] = "yahoo"
    account_label: str = "default"

    # “desired end state” + rules
    target_folders: List[str] = Field(default_factory=list)
    rules: List[MoveRule] = Field(default_factory=list)

    # guardrails
    protected_folders: List[str] = Field(
        default_factory=lambda: ["Inbox", "Sent", "Trash", "Drafts", "Spam"]
    )
    last_updated_utc: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


def load_procedure() -> MailProcedure:
    path = procedure_path()
    if not path.exists():
        return MailProcedure()
    data = json.loads(path.read_text(encoding="utf-8"))
    return MailProcedure.model_validate(data)


def save_procedure(proc: MailProcedure) -> None:
    path = procedure_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    proc.last_updated_utc = datetime.now(timezone.utc).isoformat()
    path.write_text(proc.model_dump_json(indent=2), encoding="utf-8")
