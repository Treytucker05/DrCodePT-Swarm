"""
Approval Gate - Human approval for risky operations.

This module requires human confirmation before executing potentially
dangerous operations like:
- Deleting files
- Running shell commands that modify system state
- Sending emails
- Making API calls that create/modify data
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Callable, List, Optional

logger = logging.getLogger(__name__)


class ApprovalResult(str, Enum):
    """Result of an approval request."""
    APPROVED = "approved"
    DENIED = "denied"
    TIMEOUT = "timeout"
    NOT_REQUIRED = "not_required"


class OperationType(str, Enum):
    """Types of operations that may need approval."""
    FILE_DELETE = "file_delete"
    FILE_MODIFY = "file_modify"
    SHELL_COMMAND = "shell_command"
    SEND_EMAIL = "send_email"
    API_MUTATE = "api_mutate"
    BROWSER_NAVIGATE = "browser_navigate"
    SYSTEM_MODIFY = "system_modify"
    CREDENTIAL_ACCESS = "credential_access"


# Operations that always require approval
ALWAYS_REQUIRE_APPROVAL = {
    OperationType.FILE_DELETE,
    OperationType.SYSTEM_MODIFY,
    OperationType.CREDENTIAL_ACCESS,
}

# Operations that are usually safe
USUALLY_SAFE = {
    OperationType.BROWSER_NAVIGATE,
}


@dataclass
class ApprovalRequest:
    """Request for human approval."""
    operation_type: OperationType
    description: str
    details: str = ""
    risk_level: str = "medium"
    reversible: bool = True


class ApprovalGate:
    """
    Gate that requires human approval for risky operations.

    Usage:
        gate = ApprovalGate(on_approval_request=ask_user)

        # Check if approval needed
        if gate.needs_approval(OperationType.FILE_DELETE, "Delete important.txt"):
            result = gate.request_approval(request)
            if result != ApprovalResult.APPROVED:
                return  # Don't proceed

        # Proceed with operation
        delete_file("important.txt")
    """

    def __init__(
        self,
        on_approval_request: Optional[Callable[[ApprovalRequest], bool]] = None,
        enabled: bool = True,
        auto_approve_safe: bool = True,
    ):
        """
        Initialize approval gate.

        Args:
            on_approval_request: Callback to request approval. Should return True if approved.
            enabled: Whether approvals are required.
            auto_approve_safe: Whether to auto-approve safe operations.
        """
        self.on_approval_request = on_approval_request
        self.enabled = enabled
        self.auto_approve_safe = auto_approve_safe
        self._approved_patterns: List[str] = []  # Patterns that were approved for this session

    def needs_approval(
        self,
        operation_type: OperationType,
        description: str,
    ) -> bool:
        """
        Check if an operation needs approval.

        Args:
            operation_type: Type of operation
            description: Description of the specific operation

        Returns:
            True if approval is needed
        """
        if not self.enabled:
            return False

        # Always require approval for dangerous operations
        if operation_type in ALWAYS_REQUIRE_APPROVAL:
            return True

        # Auto-approve safe operations
        if self.auto_approve_safe and operation_type in USUALLY_SAFE:
            return False

        # Check if this pattern was already approved
        for pattern in self._approved_patterns:
            if pattern in description.lower():
                return False

        return True

    def request_approval(
        self,
        request: ApprovalRequest,
    ) -> ApprovalResult:
        """
        Request approval for an operation.

        Args:
            request: The approval request details

        Returns:
            ApprovalResult indicating the outcome
        """
        if not self.enabled:
            return ApprovalResult.NOT_REQUIRED

        if not self.on_approval_request:
            logger.warning("Approval requested but no callback configured")
            return ApprovalResult.DENIED

        try:
            # Build approval message
            message = self._format_request(request)
            logger.info(f"Requesting approval: {request.description}")

            # Ask for approval
            approved = self.on_approval_request(request)

            if approved:
                logger.info(f"Approved: {request.description}")
                return ApprovalResult.APPROVED
            else:
                logger.info(f"Denied: {request.description}")
                return ApprovalResult.DENIED

        except Exception as e:
            logger.error(f"Approval request failed: {e}")
            return ApprovalResult.DENIED

    def _format_request(self, request: ApprovalRequest) -> str:
        """Format an approval request for display."""
        lines = [
            f"Operation: {request.operation_type.value}",
            f"Description: {request.description}",
        ]
        if request.details:
            lines.append(f"Details: {request.details}")
        lines.append(f"Risk Level: {request.risk_level}")
        lines.append(f"Reversible: {'Yes' if request.reversible else 'No'}")
        return "\n".join(lines)

    def approve_pattern(self, pattern: str) -> None:
        """
        Approve a pattern for the current session.

        All operations matching this pattern will be auto-approved.
        """
        self._approved_patterns.append(pattern.lower())
        logger.info(f"Pattern approved for session: {pattern}")

    def clear_approvals(self) -> None:
        """Clear all session approvals."""
        self._approved_patterns.clear()

    @staticmethod
    def console_approval_callback(request: ApprovalRequest) -> bool:
        """
        Default console-based approval callback.

        Prompts user in console for approval.
        """
        print("\n" + "=" * 60)
        print("APPROVAL REQUIRED")
        print("=" * 60)
        print(f"Operation: {request.operation_type.value}")
        print(f"Description: {request.description}")
        if request.details:
            print(f"Details: {request.details}")
        print(f"Risk Level: {request.risk_level}")
        print(f"Reversible: {'Yes' if request.reversible else 'No'}")
        print("=" * 60)

        while True:
            response = input("Approve this operation? (yes/no): ").strip().lower()
            if response in ("yes", "y"):
                return True
            elif response in ("no", "n"):
                return False
            print("Please enter 'yes' or 'no'")


# Default instance
_default_gate: Optional[ApprovalGate] = None


def get_approval_gate() -> ApprovalGate:
    """Get the default approval gate instance."""
    global _default_gate
    if _default_gate is None:
        _default_gate = ApprovalGate()
    return _default_gate


def require_approval(
    operation_type: OperationType,
    description: str,
    details: str = "",
    risk_level: str = "medium",
    reversible: bool = True,
) -> ApprovalResult:
    """
    Convenience function to request approval.

    Returns ApprovalResult.APPROVED if approved or not required.
    """
    gate = get_approval_gate()

    if not gate.needs_approval(operation_type, description):
        return ApprovalResult.NOT_REQUIRED

    request = ApprovalRequest(
        operation_type=operation_type,
        description=description,
        details=details,
        risk_level=risk_level,
        reversible=reversible,
    )

    return gate.request_approval(request)
