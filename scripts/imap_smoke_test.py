"""
Yahoo IMAP smoke test (safe-by-default).
- Dry-run: connects, lists folders, previews how many messages match your query
- Execute: creates a test folder (if missing) and moves up to N messages into it

Set env vars (recommended):
  YAHOO_IMAP_USER="you@yahoo.com"
  YAHOO_IMAP_PASS="app-password-here"

Examples:
  python scripts/imap_smoke_test.py --list-folders
  python scripts/imap_smoke_test.py --source INBOX --from-contains amazon --test-folder AgentTest
  python scripts/imap_smoke_test.py --source INBOX --subject-contains receipt --test-folder AgentTest --execute --max-move 1
"""

from __future__ import annotations

import argparse
import imaplib
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple


DEFAULT_HOST = "imap.mail.yahoo.com"
DEFAULT_PORT = 993


def _decode_bytes(x):
    if isinstance(x, bytes):
        return x.decode(errors="replace")
    return str(x)


def list_folders(imap: imaplib.IMAP4_SSL) -> List[str]:
    typ, data = imap.list()
    if typ != "OK":
        raise RuntimeError(f"LIST failed: {typ} {data}")
    folders: List[str] = []
    for line in data:
        if not line:
            continue
        b = line if isinstance(line, (bytes, bytearray)) else str(line).encode()
        # typical: b'(\\HasNoChildren) "/" "INBOX"'
        m = re.search(rb'"([^"]+)"\s*$', b)
        if m:
            folders.append(m.group(1).decode(errors="replace"))
        else:
            # fallback: last token
            folders.append(_decode_bytes(b).split()[-1].strip('"'))
    return folders


def folder_exists(folders: List[str], name: str) -> bool:
    return any(f.lower() == name.lower() for f in folders)


def ensure_folder(imap: imaplib.IMAP4_SSL, name: str, execute: bool) -> None:
    folders = list_folders(imap)
    if folder_exists(folders, name):
        print(f"[OK] Folder exists: {name}")
        return
    print(f"[PLAN] Create folder: {name}")
    if not execute:
        print("[DRY] Not creating (dry-run).")
        return
    typ, data = imap.create(name)
    if typ != "OK":
        raise RuntimeError(f"CREATE failed for {name}: {typ} {data}")
    print(f"[OK] Created folder: {name}")


def build_search_query(from_contains: Optional[str], subject_contains: Optional[str]) -> str:
    if from_contains and subject_contains:
        # simple AND
        return f'(FROM "{from_contains}" SUBJECT "{subject_contains}")'
    if from_contains:
        return f'(FROM "{from_contains}")'
    if subject_contains:
        return f'(SUBJECT "{subject_contains}")'
    # fallback: all messages
    return "ALL"


def search_uids(imap: imaplib.IMAP4_SSL, source_folder: str, query: str) -> List[str]:
    typ, _ = imap.select(source_folder, readonly=True)
    if typ != "OK":
        raise RuntimeError(f"SELECT failed for {source_folder}: {typ}")
    typ, data = imap.uid("SEARCH", None, query)
    if typ != "OK":
        raise RuntimeError(f"SEARCH failed: {typ} {data}")
    raw = data[0] if data else b""
    if isinstance(raw, bytes):
        raw = raw.decode(errors="replace")
    uids = [u for u in raw.split() if u.strip()]
    return uids


def move_uid(imap: imaplib.IMAP4_SSL, source_folder: str, uid: str, dest_folder: str) -> Tuple[bool, str]:
    # Need RW for COPY+DELETE fallback
    typ, _ = imap.select(source_folder, readonly=False)
    if typ != "OK":
        return False, f"SELECT RW failed for {source_folder}: {typ}"

    # Try MOVE extension first
    typ, data = imap.uid("MOVE", uid, dest_folder)
    if typ == "OK":
        return True, "MOVE"

    # Fallback: COPY + \Deleted + EXPUNGE
    typ, data = imap.uid("COPY", uid, dest_folder)
    if typ != "OK":
        return False, f"COPY failed: {typ} {data}"

    typ, data = imap.uid("STORE", uid, "+FLAGS.SILENT", r"(\\Deleted)")
    if typ != "OK":
        return False, f"STORE \\Deleted failed: {typ} {data}"

    imap.expunge()
    return True, "COPY+DELETE"


def write_report(path: Path, lines: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default=DEFAULT_HOST)
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--user", default=os.getenv("YAHOO_IMAP_USER", ""))
    ap.add_argument("--password", default=os.getenv("YAHOO_IMAP_PASS", ""))
    ap.add_argument("--list-folders", action="store_true")
    ap.add_argument("--source", default="INBOX")
    ap.add_argument("--test-folder", default="AgentTest")
    ap.add_argument("--from-contains", default=None)
    ap.add_argument("--subject-contains", default=None)
    ap.add_argument("--max-move", type=int, default=1)
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--report", default="runs/imap_smoke_report.md")
    args = ap.parse_args()

    if not args.user or not args.password:
        raise SystemExit("Missing credentials. Set YAHOO_IMAP_USER and YAHOO_IMAP_PASS (app password).")

    report_lines: List[str] = []
    report_lines.append("# IMAP Smoke Test Report")
    report_lines.append(f"- time_utc: {datetime.now(timezone.utc).isoformat()}")
    report_lines.append(f"- host: {args.host}:{args.port}")
    report_lines.append(f"- source: {args.source}")
    report_lines.append(f"- test_folder: {args.test_folder}")
    report_lines.append(f"- execute: {args.execute}")
    report_lines.append("")

    imap = imaplib.IMAP4_SSL(args.host, args.port)
    try:
        typ, _ = imap.login(args.user, args.password)
        if typ != "OK":
            raise RuntimeError("LOGIN failed")
        print("[OK] Logged in.")

        folders = list_folders(imap)
        print(f"[OK] Folders found: {len(folders)}")
        report_lines.append(f"## Folders ({len(folders)})")
        report_lines.extend([f"- {f}" for f in folders[:50]])
        report_lines.append("")

        if args.list_folders:
            write_report(Path(args.report), report_lines)
            print(f"[OK] Wrote report: {args.report}")
            return 0

        ensure_folder(imap, args.test_folder, execute=args.execute)

        query = build_search_query(args.from_contains, args.subject_contains)
        uids = search_uids(imap, args.source, query)
        print(f"[OK] Query: {query}")
        print(f"[OK] Matches in {args.source}: {len(uids)}")
        report_lines.append("## Search")
        report_lines.append(f"- query: `{query}`")
        report_lines.append(f"- matches: {len(uids)}")
        report_lines.append("")

        if not args.execute:
            print("[DRY] No moves performed (dry-run).")
            write_report(Path(args.report), report_lines)
            print(f"[OK] Wrote report: {args.report}")
            return 0

        moved = 0
        for uid in uids[: max(0, args.max_move)]:
            ok, method = move_uid(imap, args.source, uid, args.test_folder)
            if ok:
                moved += 1
                print(f"[OK] Moved UID {uid} -> {args.test_folder} via {method}")
                report_lines.append(f"- moved: uid={uid} method={method}")
            else:
                print(f"[ERR] Failed to move UID {uid}: {method}")
                report_lines.append(f"- failed: uid={uid} error={method}")

        report_lines.append("")
        report_lines.append("## Summary")
        report_lines.append(f"- moved: {moved} (max_move={args.max_move})")

        write_report(Path(args.report), report_lines)
        print(f"[OK] Wrote report: {args.report}")
        return 0

    finally:
        try:
            imap.logout()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
