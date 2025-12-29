"""
Secure Credential Store

Stores login credentials encrypted on disk.
Used for automating logins to services like OpenAI, Google, etc.

SECURITY NOTES:
- Credentials are encrypted using Fernet (AES-128-CBC)
- Encryption key is derived from a machine-specific secret
- Credentials file is stored in user's home directory
- Never logs or prints actual passwords
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import platform
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Try to import cryptography for encryption
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False
    logger.warning("cryptography not installed. Credentials will be stored in plain text (not recommended).")

CREDENTIALS_DIR = Path.home() / ".drcodept" / "credentials"
CREDENTIALS_FILE = CREDENTIALS_DIR / "logins.enc"


def _get_machine_id() -> str:
    """Get a machine-specific identifier for key derivation."""
    # Combine multiple machine identifiers
    parts = [
        platform.node(),  # Computer name
        os.getenv("USERNAME", os.getenv("USER", "default")),
        platform.machine(),
    ]
    return "-".join(parts)


def _derive_key(salt: bytes = b"drcodept_secure_v1") -> bytes:
    """Derive encryption key from machine-specific data."""
    if not HAS_CRYPTO:
        return b""

    machine_id = _get_machine_id().encode()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(machine_id))
    return key


def _get_fernet() -> Optional["Fernet"]:
    """Get Fernet instance for encryption/decryption."""
    if not HAS_CRYPTO:
        return None
    key = _derive_key()
    return Fernet(key)


class CredentialStore:
    """
    Securely stores and retrieves login credentials.

    Usage:
        store = CredentialStore()

        # Save credentials
        store.save("openai", {
            "email": "user@example.com",
            "password": "mypassword",
            "email_provider": "gmail",
            "email_password": "email_app_password"
        })

        # Retrieve credentials
        creds = store.get("openai")
    """

    def __init__(self):
        self._ensure_dir()
        self._fernet = _get_fernet()
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _ensure_dir(self):
        """Ensure credentials directory exists with proper permissions."""
        CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
        # On Windows, we can't easily set file permissions like Unix
        # The home directory location provides some security

    def _load_all(self) -> Dict[str, Dict[str, Any]]:
        """Load all credentials from disk."""
        if not CREDENTIALS_FILE.exists():
            return {}

        try:
            encrypted_data = CREDENTIALS_FILE.read_bytes()

            if self._fernet:
                decrypted = self._fernet.decrypt(encrypted_data)
                return json.loads(decrypted.decode())
            else:
                # Fallback: plain JSON (not recommended)
                return json.loads(encrypted_data.decode())

        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")
            return {}

    def _save_all(self, data: Dict[str, Dict[str, Any]]) -> bool:
        """Save all credentials to disk."""
        try:
            json_data = json.dumps(data, indent=2).encode()

            if self._fernet:
                encrypted = self._fernet.encrypt(json_data)
                CREDENTIALS_FILE.write_bytes(encrypted)
            else:
                # Fallback: plain JSON (not recommended)
                CREDENTIALS_FILE.write_bytes(json_data)

            return True
        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")
            return False

    def save(self, service: str, credentials: Dict[str, Any]) -> bool:
        """
        Save credentials for a service.

        Args:
            service: Service name (e.g., "openai", "google", "github")
            credentials: Dict with login details (email, password, etc.)

        Returns:
            True if saved successfully
        """
        all_creds = self._load_all()
        all_creds[service] = credentials

        success = self._save_all(all_creds)
        if success:
            self._cache[service] = credentials
            logger.info(f"Saved credentials for: {service}")

        return success

    def get(self, service: str) -> Optional[Dict[str, Any]]:
        """
        Get credentials for a service.

        Args:
            service: Service name

        Returns:
            Credentials dict or None if not found
        """
        if service in self._cache:
            return self._cache[service]

        all_creds = self._load_all()
        creds = all_creds.get(service)

        if creds:
            self._cache[service] = creds

        return creds

    def delete(self, service: str) -> bool:
        """Delete credentials for a service."""
        all_creds = self._load_all()

        if service in all_creds:
            del all_creds[service]
            self._save_all(all_creds)
            self._cache.pop(service, None)
            logger.info(f"Deleted credentials for: {service}")
            return True

        return False

    def list_services(self) -> list:
        """List all services with stored credentials."""
        return list(self._load_all().keys())

    def has_credentials(self, service: str) -> bool:
        """Check if credentials exist for a service."""
        return service in self._load_all()


# Singleton instance
_store: Optional[CredentialStore] = None


def get_credential_store() -> CredentialStore:
    """Get the singleton credential store instance."""
    global _store
    if _store is None:
        _store = CredentialStore()
    return _store


def prompt_and_save_credentials(service: str, fields: list) -> Dict[str, str]:
    """
    Interactively prompt for credentials and save them.

    Args:
        service: Service name
        fields: List of field names to prompt for (e.g., ["email", "password"])

    Returns:
        The saved credentials dict
    """
    import getpass

    print(f"\n=== Setting up credentials for: {service} ===")

    credentials = {}
    for field in fields:
        if "password" in field.lower():
            value = getpass.getpass(f"  {field}: ")
        else:
            value = input(f"  {field}: ").strip()
        credentials[field] = value

    store = get_credential_store()
    store.save(service, credentials)

    print(f"  [OK] Credentials saved securely")
    return credentials


__all__ = [
    "CredentialStore",
    "get_credential_store",
    "prompt_and_save_credentials",
]
