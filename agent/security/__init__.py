"""
Security Module - Safety controls for the agent.

This module provides:
- KillSwitch: Emergency stop mechanism
- ApprovalGate: Human approval for risky operations
- SecretStore: Secure credential storage
- Allowlists: Domain and tool restrictions
- Redactor: Secret removal from logs/traces
"""

from .kill_switch import KillSwitch, check_kill_switch
from .approvals import ApprovalGate, ApprovalResult
from .secret_store import SecretStore, get_secret_store
from .allowlists import DomainAllowlist, ToolAllowlist
from .redactor import Redactor, redact_secrets

__all__ = [
    "KillSwitch",
    "check_kill_switch",
    "ApprovalGate",
    "ApprovalResult",
    "SecretStore",
    "get_secret_store",
    "DomainAllowlist",
    "ToolAllowlist",
    "Redactor",
    "redact_secrets",
]
