from __future__ import annotations

"""Encrypted credential store for site logins.

Credentials are stored as encrypted tokens on disk and referenced by ID from
agent_memory.json. An encryption key is loaded from the AGENT_CREDENTIAL_KEY
environment variable when available; otherwise a persistent key file is
created automatically so credentials can be saved without manual setup.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4

from cryptography.fernet import Fernet, InvalidToken

from .memory_manager import load_memory, save_memory

ROOT = Path(__file__).resolve().parent
STORE_PATH = ROOT / "credential_store.json"
KEY_ENV_VAR = "AGENT_CREDENTIAL_KEY"
KEY_FILE = ROOT / "credential_key.key"


class CredentialError(RuntimeError):
    """Raised when credential operations fail."""


def _load_key() -> bytes:
    env_key = os.getenv(KEY_ENV_VAR)
    if env_key:
        return env_key.encode("utf-8")

    if KEY_FILE.is_file():
        return KEY_FILE.read_bytes()

    new_key = Fernet.generate_key()
    KEY_FILE.write_bytes(new_key)
    try:
        os.chmod(KEY_FILE, 0o600)
    except OSError:
        pass
    return new_key


def _fernet() -> Fernet:
    key = _load_key()
    try:
        return Fernet(key)
    except Exception as exc:  # pragma: no cover - invalid key handling
        raise CredentialError("Invalid credential key; ensure it is a valid Fernet key.") from exc


def _load_store() -> Dict[str, Any]:
    if not STORE_PATH.is_file():
        return {"version": 1, "entries": {}}
    try:
        return json.loads(STORE_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        raise CredentialError(f"Unable to read credential store: {exc}") from exc


def _save_store(data: Dict[str, Any]) -> None:
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STORE_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def save_credential(site: str, username: str, password: str) -> str:
    """Encrypt and persist credentials for a site.

    Returns the credential_id used to reference the stored entry.
    """

    if not site:
        raise CredentialError("Site name is required to save credentials.")

    cipher = _fernet()
    payload = json.dumps({"username": username, "password": password}, ensure_ascii=False).encode(
        "utf-8"
    )
    token = cipher.encrypt(payload).decode("utf-8")

    store = _load_store()
    entries = store.setdefault("entries", {})

    memory = load_memory()
    credential_id = memory.get("credentials", {}).get(site) or f"{site}-{uuid4().hex[:8]}"

    entries[credential_id] = {
        "site": site,
        "token": token,
        "updated_at": datetime.utcnow().isoformat(),
    }
    store["version"] = 1
    _save_store(store)

    memory.setdefault("credentials", {})[site] = credential_id
    save_memory(memory)

    return credential_id


def get_credential(site: str) -> Optional[Dict[str, str]]:
    """Retrieve decrypted credentials for a site.

    Returns a dict with ``username`` and ``password`` keys, or None if missing.
    """

    if not site:
        raise CredentialError("Site name is required to load credentials.")

    credential_id = (load_memory().get("credentials") or {}).get(site)
    if not credential_id:
        return None

    store = _load_store()
    entry = (store.get("entries") or {}).get(credential_id)
    if not entry:
        return None

    token = entry.get("token")
    if not token:
        return None

    cipher = _fernet()
    try:
        decrypted = cipher.decrypt(token.encode("utf-8"))
    except InvalidToken:
        raise CredentialError("Failed to decrypt credentials: invalid key or corrupted data.")

    data = json.loads(decrypted)
    return {"username": data.get("username", ""), "password": data.get("password", "")}


def build_login_steps(site: str, start_url: Optional[str] = None) -> list[Dict[str, Any]]:
    """Construct browser steps for the site's login_flow using stored credentials."""

    creds = get_credential(site)
    if not creds:
        raise CredentialError(
            f"No credentials stored for '{site}'. Call save_credential(site, username, password) first."
        )

    try:
        from agent.learning.learning_store import load_playbook
    except Exception as exc:  # pragma: no cover - late import guard
        raise CredentialError(f"Unable to load playbook for {site}: {exc}") from exc

    playbook = load_playbook(site)
    flow = playbook.get("login_flow") or []
    if not flow:
        raise CredentialError(f"No login_flow defined for site '{site}'.")

    steps: list[Dict[str, Any]] = []
    start = start_url or playbook.get("start_url")
    if start:
        steps.append({"action": "goto", "url": start})

    username = creds.get("username", "")
    password = creds.get("password", "")

    for item in flow:
        action = item.get("action")
        selector = item.get("selector")
        timeout = item.get("timeout_ms")

        if action == "fill":
            field_type = (item.get("field_type") or "").lower()
            value = password if field_type == "password" else username
            step: Dict[str, Any] = {"action": "fill", "selector": selector, "value": value}
            if timeout is not None:
                step["timeout_ms"] = timeout
            steps.append(step)
            continue

        if action == "click":
            step = {"action": "click"}
            if selector:
                step["selector"] = selector
            if item.get("text"):
                step["text"] = item["text"]
            if timeout is not None:
                step["timeout_ms"] = timeout
            steps.append(step)
            continue

        if action == "submit":
            step = {"action": "press", "key": "Enter"}
            if selector:
                step["selector"] = selector
            steps.append(step)
            continue

        # Pass through unhandled actions with minimal keys
        pass_through = {"action": action}
        if selector:
            pass_through["selector"] = selector
        if timeout is not None:
            pass_through["timeout_ms"] = timeout
        steps.append(pass_through)

    return steps


__all__ = [
    "build_login_steps",
    "CredentialError",
    "get_credential",
    "save_credential",
    "STORE_PATH",
    "KEY_ENV_VAR",
]
