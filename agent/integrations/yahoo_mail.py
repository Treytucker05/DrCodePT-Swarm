from __future__ import annotations

"""Yahoo Mail IMAP/SMTP helpers (app-password based)."""

import imaplib
import re
import smtplib
from email.header import decode_header
from email.message import EmailMessage
from email.parser import BytesParser
from email.policy import default
from typing import Any, Dict, List, Optional

from agent.memory.credentials import get_credential

IMAP_HOST = "imap.mail.yahoo.com"
IMAP_PORT = 993
SMTP_HOST = "smtp.mail.yahoo.com"
SMTP_PORT_SSL = 465


def _decode(value: Optional[str]) -> str:
    if not value:
        return ""
    parts = decode_header(value)
    decoded: List[str] = []
    for text, enc in parts:
        if isinstance(text, bytes):
            try:
                decoded.append(text.decode(enc or "utf-8", errors="replace"))
            except Exception:
                decoded.append(text.decode("utf-8", errors="replace"))
        else:
            decoded.append(text)
    return "".join(decoded)


def _load_creds(site_key: str = "yahoo_imap") -> Dict[str, str]:
    creds = get_credential(site_key)
    if not creds:
        raise RuntimeError(
            "No Yahoo IMAP credentials stored. Run: Cred: yahoo_imap (use your Yahoo email + app password)"
        )
    username = creds.get("username", "").strip()
    password = creds.get("password", "").strip()
    # Yahoo app passwords are often displayed with spaces; normalize to plain token.
    if password:
        password = password.replace(" ", "").replace("-", "")
    if not username or not password:
        raise RuntimeError("Yahoo IMAP credentials are incomplete.")
    return {"username": username, "password": password}


def _imap_login():
    creds = _load_creds()
    imap = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    imap.login(creds["username"], creds["password"])
    return imap


def _parse_quoted(value: str) -> str:
    if not value.startswith('"'):
        return value
    out = []
    i = 1
    while i < len(value):
        ch = value[i]
        if ch == '"':
            break
        if ch == "\\" and i + 1 < len(value):
            out.append(value[i + 1])
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def _parse_mailbox(line: str) -> str:
    # Typical IMAP LIST response: '(\\HasNoChildren) "/" "INBOX"'
    # Some servers omit quotes for simple names: '(\\HasNoChildren) "/" INBOX'
    m = re.search(r'\\)\\s+"[^"]*"\\s+(.+)$', line)
    name = m.group(1).strip() if m else line.strip().split()[-1]
    if name.startswith('"'):
        return _parse_quoted(name)
    if name.startswith("{"):
        # Literal; best-effort fallback
        return name
    return name


def _quote_mailbox(name: str) -> str:
    if name.startswith('"') and name.endswith('"') and len(name) >= 2:
        name = name[1:-1]
    name = name.replace("\\", "\\\\").replace('"', '\\"')
    return f"\"{name}\""


def list_folders() -> List[str]:
    """Return a list of mailbox folders for the account."""
    with _imap_login() as imap:
        status, data = imap.list()
        if status != "OK" or not data:
            raise RuntimeError("Failed to list folders.")
        folders: List[str] = []
        for item in data:
            if not item:
                continue
            line = item.decode("utf-8", errors="replace") if isinstance(item, bytes) else str(item)
            name = _parse_mailbox(line)
            if name:
                folders.append(name)
        return folders


def folder_counts(folders: Optional[List[str]] = None) -> Dict[str, int]:
    """Return message counts per folder (best-effort)."""
    with _imap_login() as imap:
        if folders is None:
            status, data = imap.list()
            if status != "OK" or not data:
                raise RuntimeError("Failed to list folders.")
            folders = []
            for item in data:
                if not item:
                    continue
                line = item.decode("utf-8", errors="replace") if isinstance(item, bytes) else str(item)
                name = _parse_mailbox(line)
                if name:
                    folders.append(name)
        counts: Dict[str, int] = {}
        for folder in folders:
            try:
                status, data = imap.select(_quote_mailbox(folder), readonly=True)
                if status == "OK" and data:
                    counts[folder] = int(data[0])
                else:
                    counts[folder] = 0
            except Exception:
                counts[folder] = 0
        return counts


def iter_headers(
    *,
    folder: str = "INBOX",
    limit: Optional[int] = None,
    progress_cb=None,
) -> List[Dict[str, Any]]:
    """Fetch message headers for a folder (optionally limit to newest N)."""
    results: List[Dict[str, Any]] = []
    with _imap_login() as imap:
        status, _ = imap.select(_quote_mailbox(folder), readonly=True)
        if status != "OK":
            raise RuntimeError(f"Failed to select folder {folder}: {status}")
        status, data = imap.search(None, "ALL")
        if status != "OK" or not data or not data[0]:
            return []
        ids = data[0].split()
        if limit:
            ids = ids[-limit:]
        total = len(ids)
        for idx, uid in enumerate(ids, 1):
            status, msg_data = imap.fetch(uid, "(RFC822.HEADER)")
            if status != "OK" or not msg_data:
                continue
            header_bytes = msg_data[0][1]
            msg = BytesParser(policy=default).parsebytes(header_bytes)
            results.append(
                {
                    "uid": uid.decode("utf-8", errors="ignore"),
                    "from": _decode(msg.get("From")),
                    "to": _decode(msg.get("To")),
                    "subject": _decode(msg.get("Subject")),
                    "date": _decode(msg.get("Date")),
                    "message_id": _decode(msg.get("Message-ID")),
                    "folder": folder,
                }
            )
            if progress_cb and (idx % 200 == 0 or idx == total):
                progress_cb(folder, idx, total)
    return results


def list_messages(limit: int = 5, folder: str = "INBOX") -> List[Dict[str, Any]]:
    creds = _load_creds()
    with imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT) as imap:
        imap.login(creds["username"], creds["password"])
        status, _ = imap.select(folder, readonly=True)
        if status != "OK":
            raise RuntimeError(f"Failed to select folder {folder}: {status}")
        status, data = imap.search(None, "ALL")
        if status != "OK" or not data or not data[0]:
            return []
        ids = data[0].split()
        last = ids[-limit:]
        results: List[Dict[str, Any]] = []
        for uid in reversed(last):
            status, msg_data = imap.fetch(uid, "(RFC822.HEADER)")
            if status != "OK" or not msg_data:
                continue
            header_bytes = msg_data[0][1]
            msg = BytesParser(policy=default).parsebytes(header_bytes)
            results.append(
                {
                    "uid": uid.decode("utf-8", errors="ignore"),
                    "from": _decode(msg.get("From")),
                    "to": _decode(msg.get("To")),
                    "subject": _decode(msg.get("Subject")),
                    "date": _decode(msg.get("Date")),
                    "message_id": _decode(msg.get("Message-ID")),
                }
            )
        return results


def read_message(uid: str, folder: str = "INBOX") -> Dict[str, Any]:
    creds = _load_creds()
    with imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT) as imap:
        imap.login(creds["username"], creds["password"])
        status, _ = imap.select(folder, readonly=True)
        if status != "OK":
            raise RuntimeError(f"Failed to select folder {folder}: {status}")
        status, msg_data = imap.fetch(uid, "(RFC822)")
        if status != "OK" or not msg_data:
            raise RuntimeError(f"Failed to fetch message {uid}")
        msg_bytes = msg_data[0][1]
        msg = BytesParser(policy=default).parsebytes(msg_bytes)

    body_text = ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = (part.get("Content-Disposition") or "").lower()
            if ctype == "text/plain" and "attachment" not in disp:
                body_text = part.get_content().strip()
                break
    else:
        if msg.get_content_type() == "text/plain":
            body_text = msg.get_content().strip()

    return {
        "uid": uid,
        "from": _decode(msg.get("From")),
        "to": _decode(msg.get("To")),
        "subject": _decode(msg.get("Subject")),
        "date": _decode(msg.get("Date")),
        "message_id": _decode(msg.get("Message-ID")),
        "body": body_text,
    }


def send_message(
    to_addrs: List[str],
    subject: str,
    body: str,
    *,
    cc_addrs: Optional[List[str]] = None,
    bcc_addrs: Optional[List[str]] = None,
    reply_to: Optional[str] = None,
) -> Dict[str, Any]:
    creds = _load_creds()
    msg = EmailMessage()
    msg["From"] = creds["username"]
    msg["To"] = ", ".join(to_addrs)
    if cc_addrs:
        msg["Cc"] = ", ".join(cc_addrs)
    if reply_to:
        msg["Reply-To"] = reply_to
    msg["Subject"] = subject
    msg.set_content(body)

    recipients = list(to_addrs)
    if cc_addrs:
        recipients.extend(cc_addrs)
    if bcc_addrs:
        recipients.extend(bcc_addrs)

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT_SSL) as smtp:
        smtp.login(creds["username"], creds["password"])
        smtp.send_message(msg, to_addrs=recipients)

    return {"to": recipients, "subject": subject}
