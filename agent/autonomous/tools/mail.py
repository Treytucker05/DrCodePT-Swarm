from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from agent.integrations import yahoo_mail
from agent.autonomous.models import ToolResult
from agent.autonomous.config import RunContext


class MailArgs(BaseModel):
    provider: str = Field(default="yahoo", description="email provider (currently: yahoo)")
    action: str = Field(description="list | read | send")
    folder: str = Field(default="INBOX")
    limit: int = Field(default=5, ge=1, le=50)
    uid: Optional[str] = None
    to: Optional[List[str]] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    reply_to: Optional[str] = None
    confirm: bool = False


def mail_tool(ctx: RunContext, args: MailArgs) -> ToolResult:
    provider = (args.provider or "").lower().strip()
    action = (args.action or "").lower().strip()

    if provider != "yahoo":
        return ToolResult(success=False, error=f"Unsupported provider: {provider}")

    try:
        if action == "list":
            items = yahoo_mail.list_messages(limit=args.limit, folder=args.folder)
            return ToolResult(success=True, output={"messages": items})

        if action == "read":
            if not args.uid:
                return ToolResult(success=False, error="read requires uid")
            msg = yahoo_mail.read_message(uid=str(args.uid), folder=args.folder)
            return ToolResult(success=True, output={"message": msg})

        if action == "send":
            if not args.confirm:
                return ToolResult(
                    success=False,
                    error="confirmation_required",
                    metadata={"hint": "Set confirm=true after user approval to send."},
                )
            if not args.to or not args.subject or not args.body:
                return ToolResult(success=False, error="send requires to, subject, body")
            result = yahoo_mail.send_message(
                to_addrs=args.to,
                subject=args.subject or "",
                body=args.body or "",
                cc_addrs=args.cc,
                bcc_addrs=args.bcc,
                reply_to=args.reply_to,
            )
            return ToolResult(success=True, output={"sent": result})

        return ToolResult(success=False, error=f"Unsupported action: {action}")
    except Exception as exc:
        return ToolResult(success=False, error=str(exc))
