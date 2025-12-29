"""
Secret Store - Secure credential storage.

This module provides secure storage for API keys, tokens, and other secrets.
On Windows, it uses DPAPI for encryption. On other platforms, it uses
a file-based store with basic obfuscation (not truly secure).

NEVER log or expose secrets in traces/prompts!
"""
from __future__ import annotations

import base64
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Default secrets file path
DEFAULT_SECRETS_PATH = Path.home() / ".agent_secrets" / "secrets.json"


@dataclass
class SecretEntry:
    """A stored secret."""
    name: str
    value: str
    metadata: Dict[str, Any]


class SecretStore:
    """
    Secure storage for secrets.

    On Windows, uses DPAPI for encryption.
    """

    def __init__(self, path: Optional[Path] = None):
        """
        Initialize secret store.

        Args:
            path: Path to secrets file.
        """
        self.path = path or Path(
            os.environ.get("AGENT_SECRETS_PATH", str(DEFAULT_SECRETS_PATH))
        )
        self._cache: Dict[str, SecretEntry] = {}
        self._dpapi_available = self._check_dpapi()

    def _check_dpapi(self) -> bool:
        """Check if Windows DPAPI is available."""
        try:
            import ctypes
            ctypes.windll.crypt32
            return True
        except Exception:
            return False

    def _encrypt(self, data: str) -> str:
        """Encrypt data using DPAPI or fallback."""
        if self._dpapi_available:
            try:
                return self._dpapi_encrypt(data)
            except Exception as e:
                logger.warning(f"DPAPI encryption failed: {e}")

        # Fallback: base64 obfuscation (NOT secure, just prevents casual viewing)
        return base64.b64encode(data.encode()).decode()

    def _decrypt(self, data: str) -> str:
        """Decrypt data using DPAPI or fallback."""
        if self._dpapi_available:
            try:
                return self._dpapi_decrypt(data)
            except Exception:
                pass

        # Fallback: base64 decode
        try:
            return base64.b64decode(data.encode()).decode()
        except Exception:
            return data  # Return as-is if decryption fails

    def _dpapi_encrypt(self, data: str) -> str:
        """Encrypt using Windows DPAPI."""
        import ctypes
        from ctypes import wintypes

        class DATA_BLOB(ctypes.Structure):
            _fields_ = [
                ("cbData", wintypes.DWORD),
                ("pbData", ctypes.POINTER(ctypes.c_char)),
            ]

        crypt32 = ctypes.windll.crypt32
        kernel32 = ctypes.windll.kernel32

        # Prepare input
        data_bytes = data.encode("utf-8")
        input_blob = DATA_BLOB(len(data_bytes), ctypes.cast(
            ctypes.create_string_buffer(data_bytes),
            ctypes.POINTER(ctypes.c_char)
        ))
        output_blob = DATA_BLOB()

        # Encrypt
        if not crypt32.CryptProtectData(
            ctypes.byref(input_blob),
            None,  # Description
            None,  # Entropy
            None,  # Reserved
            None,  # Prompt
            0,     # Flags
            ctypes.byref(output_blob),
        ):
            raise Exception("CryptProtectData failed")

        # Get encrypted data
        encrypted = ctypes.string_at(output_blob.pbData, output_blob.cbData)
        kernel32.LocalFree(output_blob.pbData)

        return base64.b64encode(encrypted).decode()

    def _dpapi_decrypt(self, data: str) -> str:
        """Decrypt using Windows DPAPI."""
        import ctypes
        from ctypes import wintypes

        class DATA_BLOB(ctypes.Structure):
            _fields_ = [
                ("cbData", wintypes.DWORD),
                ("pbData", ctypes.POINTER(ctypes.c_char)),
            ]

        crypt32 = ctypes.windll.crypt32
        kernel32 = ctypes.windll.kernel32

        # Prepare input
        encrypted = base64.b64decode(data.encode())
        input_blob = DATA_BLOB(len(encrypted), ctypes.cast(
            ctypes.create_string_buffer(encrypted),
            ctypes.POINTER(ctypes.c_char)
        ))
        output_blob = DATA_BLOB()

        # Decrypt
        if not crypt32.CryptUnprotectData(
            ctypes.byref(input_blob),
            None,  # Description
            None,  # Entropy
            None,  # Reserved
            None,  # Prompt
            0,     # Flags
            ctypes.byref(output_blob),
        ):
            raise Exception("CryptUnprotectData failed")

        # Get decrypted data
        decrypted = ctypes.string_at(output_blob.pbData, output_blob.cbData)
        kernel32.LocalFree(output_blob.pbData)

        return decrypted.decode("utf-8")

    def _load(self) -> None:
        """Load secrets from file."""
        if not self.path.exists():
            return

        try:
            data = json.loads(self.path.read_text())
            for name, entry in data.items():
                value = self._decrypt(entry.get("encrypted_value", ""))
                self._cache[name] = SecretEntry(
                    name=name,
                    value=value,
                    metadata=entry.get("metadata", {}),
                )
        except Exception as e:
            logger.error(f"Failed to load secrets: {e}")

    def _save(self) -> None:
        """Save secrets to file."""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)

            data = {}
            for name, entry in self._cache.items():
                data[name] = {
                    "encrypted_value": self._encrypt(entry.value),
                    "metadata": entry.metadata,
                }

            self.path.write_text(json.dumps(data, indent=2))

            # Set restrictive permissions on Windows
            if os.name == 'nt':
                import stat
                os.chmod(self.path, stat.S_IRUSR | stat.S_IWUSR)

        except Exception as e:
            logger.error(f"Failed to save secrets: {e}")

    def get(self, name: str) -> Optional[str]:
        """
        Get a secret by name.

        Args:
            name: Secret name

        Returns:
            Secret value or None if not found
        """
        if not self._cache:
            self._load()

        entry = self._cache.get(name)
        return entry.value if entry else None

    def set(
        self,
        name: str,
        value: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Store a secret.

        Args:
            name: Secret name
            value: Secret value
            metadata: Optional metadata
        """
        self._cache[name] = SecretEntry(
            name=name,
            value=value,
            metadata=metadata or {},
        )
        self._save()

    def delete(self, name: str) -> bool:
        """
        Delete a secret.

        Args:
            name: Secret name

        Returns:
            True if deleted, False if not found
        """
        if name in self._cache:
            del self._cache[name]
            self._save()
            return True
        return False

    def list_names(self) -> list[str]:
        """List all secret names (not values!)."""
        if not self._cache:
            self._load()
        return list(self._cache.keys())

    def has(self, name: str) -> bool:
        """Check if a secret exists."""
        if not self._cache:
            self._load()
        return name in self._cache


# Global instance
_default_store: Optional[SecretStore] = None


def get_secret_store() -> SecretStore:
    """Get the default secret store instance."""
    global _default_store
    if _default_store is None:
        _default_store = SecretStore()
    return _default_store


def get_secret(name: str) -> Optional[str]:
    """Get a secret by name."""
    return get_secret_store().get(name)


def set_secret(name: str, value: str, **metadata) -> None:
    """Store a secret."""
    get_secret_store().set(name, value, metadata)
