"""
Allowlists - Domain and tool restrictions.

This module enforces allowlists for:
- Browser domains (where the agent can navigate)
- Tools (which tools are permitted)
- File paths (where the agent can read/write)
"""
from __future__ import annotations

import fnmatch
import logging
import os
import re
from pathlib import Path
from typing import List, Optional, Set
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class DomainAllowlist:
    """
    Allowlist for browser navigation.

    Controls which domains the agent is allowed to visit.
    """

    # Default safe domains
    DEFAULT_ALLOWED = {
        "github.com",
        "*.github.com",
        "google.com",
        "*.google.com",
        "stackoverflow.com",
        "*.stackoverflow.com",
        "docs.python.org",
        "pypi.org",
        "npmjs.com",
        "developer.mozilla.org",
    }

    def __init__(
        self,
        allowed: Optional[Set[str]] = None,
        blocked: Optional[Set[str]] = None,
    ):
        """
        Initialize domain allowlist.

        Args:
            allowed: Set of allowed domain patterns (supports wildcards)
            blocked: Set of blocked domain patterns (takes precedence)
        """
        # Load from environment if not provided
        if allowed is None:
            env_allowed = os.environ.get("AGENT_ALLOWED_DOMAINS", "")
            if env_allowed:
                allowed = set(d.strip() for d in env_allowed.split(",") if d.strip())
            else:
                allowed = self.DEFAULT_ALLOWED.copy()

        if blocked is None:
            env_blocked = os.environ.get("AGENT_BLOCKED_DOMAINS", "")
            if env_blocked:
                blocked = set(d.strip() for d in env_blocked.split(",") if d.strip())
            else:
                blocked = set()

        self.allowed = allowed
        self.blocked = blocked
        self.enabled = os.environ.get("AGENT_DOMAIN_ALLOWLIST", "1") != "0"

    def is_allowed(self, url: str) -> bool:
        """
        Check if a URL is allowed.

        Args:
            url: URL to check

        Returns:
            True if allowed, False if blocked
        """
        if not self.enabled:
            return True

        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Remove port if present
            if ":" in domain:
                domain = domain.split(":")[0]

            # Check blocked list first (takes precedence)
            for pattern in self.blocked:
                if self._matches(domain, pattern):
                    logger.warning(f"Domain blocked: {domain} (pattern: {pattern})")
                    return False

            # Check allowed list
            for pattern in self.allowed:
                if self._matches(domain, pattern):
                    return True

            logger.warning(f"Domain not in allowlist: {domain}")
            return False

        except Exception as e:
            logger.error(f"Error checking domain: {e}")
            return False

    def _matches(self, domain: str, pattern: str) -> bool:
        """Check if domain matches pattern (supports wildcards)."""
        # Convert wildcard pattern to regex
        if pattern.startswith("*."):
            # *.example.com matches example.com and sub.example.com
            base = pattern[2:]
            return domain == base or domain.endswith("." + base)
        return domain == pattern

    def add(self, pattern: str) -> None:
        """Add a domain pattern to the allowlist."""
        self.allowed.add(pattern)
        logger.info(f"Added to domain allowlist: {pattern}")

    def remove(self, pattern: str) -> None:
        """Remove a domain pattern from the allowlist."""
        self.allowed.discard(pattern)

    def block(self, pattern: str) -> None:
        """Add a domain pattern to the blocklist."""
        self.blocked.add(pattern)
        logger.info(f"Added to domain blocklist: {pattern}")


class ToolAllowlist:
    """
    Allowlist for tool execution.

    Controls which tools the agent is allowed to use.
    """

    # Default allowed tools (safe, read-only or low-risk)
    DEFAULT_ALLOWED = {
        "read_file",
        "list_directory",
        "search_files",
        "web_search",
        "web_fetch",
        "get_calendar_events",
        "memory_query",
        "memory_store",
    }

    # Tools that always require extra approval
    SENSITIVE_TOOLS = {
        "delete_file",
        "shell_execute",
        "run_command",
        "send_email",
        "modify_system",
    }

    def __init__(
        self,
        allowed: Optional[Set[str]] = None,
        blocked: Optional[Set[str]] = None,
    ):
        """
        Initialize tool allowlist.

        Args:
            allowed: Set of allowed tool names
            blocked: Set of blocked tool names (takes precedence)
        """
        if allowed is None:
            env_allowed = os.environ.get("AGENT_ALLOWED_TOOLS", "")
            if env_allowed:
                allowed = set(t.strip() for t in env_allowed.split(",") if t.strip())
            else:
                allowed = self.DEFAULT_ALLOWED.copy()

        if blocked is None:
            env_blocked = os.environ.get("AGENT_BLOCKED_TOOLS", "")
            if env_blocked:
                blocked = set(t.strip() for t in env_blocked.split(",") if t.strip())
            else:
                blocked = set()

        self.allowed = allowed
        self.blocked = blocked
        self.allow_all = os.environ.get("AGENT_ALLOW_ALL_TOOLS", "0") == "1"

    def is_allowed(self, tool_name: str) -> bool:
        """
        Check if a tool is allowed.

        Args:
            tool_name: Name of the tool

        Returns:
            True if allowed, False if blocked
        """
        if self.allow_all:
            # Even with allow_all, check blocked list
            if tool_name in self.blocked:
                logger.warning(f"Tool blocked: {tool_name}")
                return False
            return True

        # Check blocked list first
        if tool_name in self.blocked:
            logger.warning(f"Tool blocked: {tool_name}")
            return False

        # Check allowed list
        if tool_name in self.allowed:
            return True

        # Default: block
        logger.warning(f"Tool not in allowlist: {tool_name}")
        return False

    def is_sensitive(self, tool_name: str) -> bool:
        """Check if a tool is sensitive (requires extra approval)."""
        return tool_name in self.SENSITIVE_TOOLS

    def add(self, tool_name: str) -> None:
        """Add a tool to the allowlist."""
        self.allowed.add(tool_name)

    def remove(self, tool_name: str) -> None:
        """Remove a tool from the allowlist."""
        self.allowed.discard(tool_name)

    def block(self, tool_name: str) -> None:
        """Add a tool to the blocklist."""
        self.blocked.add(tool_name)


class PathAllowlist:
    """
    Allowlist for file system access.

    Controls which paths the agent can read/write.
    """

    def __init__(
        self,
        allowed_roots: Optional[List[Path]] = None,
        allow_anywhere: bool = False,
    ):
        """
        Initialize path allowlist.

        Args:
            allowed_roots: List of allowed root directories
            allow_anywhere: If True, allow access anywhere (DANGEROUS)
        """
        if allowed_roots is None:
            env_roots = os.environ.get("AUTO_FS_ALLOWED_ROOTS", "")
            if env_roots:
                allowed_roots = [Path(p.strip()) for p in env_roots.split(";") if p.strip()]
            else:
                # Default: user's documents and downloads
                allowed_roots = [
                    Path.home() / "Documents",
                    Path.home() / "Downloads",
                    Path.cwd(),  # Current working directory
                ]

        self.allowed_roots = [p.resolve() for p in allowed_roots]
        self.allow_anywhere = allow_anywhere or os.environ.get("AUTO_FS_ANYWHERE", "0") == "1"

    def is_allowed(self, path: Path) -> bool:
        """
        Check if a path is allowed.

        Args:
            path: Path to check

        Returns:
            True if allowed
        """
        if self.allow_anywhere:
            return True

        try:
            resolved = path.resolve()

            for root in self.allowed_roots:
                try:
                    resolved.relative_to(root)
                    return True
                except ValueError:
                    continue

            logger.warning(f"Path not in allowed roots: {path}")
            return False

        except Exception as e:
            logger.error(f"Error checking path: {e}")
            return False

    def add_root(self, path: Path) -> None:
        """Add an allowed root directory."""
        self.allowed_roots.append(path.resolve())


# Global instances
_domain_allowlist: Optional[DomainAllowlist] = None
_tool_allowlist: Optional[ToolAllowlist] = None
_path_allowlist: Optional[PathAllowlist] = None


def get_domain_allowlist() -> DomainAllowlist:
    """Get the domain allowlist."""
    global _domain_allowlist
    if _domain_allowlist is None:
        _domain_allowlist = DomainAllowlist()
    return _domain_allowlist


def get_tool_allowlist() -> ToolAllowlist:
    """Get the tool allowlist."""
    global _tool_allowlist
    if _tool_allowlist is None:
        _tool_allowlist = ToolAllowlist()
    return _tool_allowlist


def get_path_allowlist() -> PathAllowlist:
    """Get the path allowlist."""
    global _path_allowlist
    if _path_allowlist is None:
        _path_allowlist = PathAllowlist()
    return _path_allowlist
