from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from agent.autonomous.memory.sqlite_store import SqliteMemoryStore
from agent.integrations import yahoo_mail


def _prompt(text: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    val = input(f"{text}{suffix}: ").strip()
    return val if val else (default or "")


def _prompt_int(text: str, default: int) -> int:
    raw = _prompt(text, str(default))
    try:
        return max(1, int(raw))
    except Exception:
        return default


def _parse_indices(raw: str, max_index: int) -> List[int]:
    if not raw:
        return []
    picks: List[int] = []
    parts = re.split(r"[,\s]+", raw.strip())
    for part in parts:
        if not part:
            continue
        if "-" in part:
            try:
                start, end = part.split("-", 1)
                for i in range(int(start), int(end) + 1):
                    if 1 <= i <= max_index:
                        picks.append(i)
            except Exception:
                continue
        else:
            try:
                i = int(part)
                if 1 <= i <= max_index:
                    picks.append(i)
            except Exception:
                continue
    return sorted(set(picks))


def _sender_domain(sender: str) -> str:
    if not sender:
        return ""
    m = re.search(r"@([A-Za-z0-9._-]+\.[A-Za-z]{2,})", sender)
    return m.group(1).lower() if m else ""


def _open_memory_store() -> SqliteMemoryStore:
    root = Path(__file__).resolve().parents[1]
    return SqliteMemoryStore(root / "memory" / "autonomous_memory.sqlite3")


def _print_header(title: str) -> None:
    bar = "-" * max(8, len(title))
    print(f"\n{bar}\n{title}\n{bar}")


def _summarize_counts(items: List[Tuple[str, int]], max_rows: int = 20) -> List[Tuple[str, int]]:
    return items[:max_rows]


def _format_sender(sender: str, width: int = 48) -> str:
    if len(sender) <= width:
        return sender
    return sender[: width - 3] + "..."


def _parse_sender_selection(raw: str, ranked: List[Tuple[str, int]]) -> Tuple[List[str], List[str]]:
    important: List[str] = []
    domains: List[str] = []
    if not raw:
        return important, domains
    parts = re.split(r"[,\n]+", raw.strip())
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if part.startswith("d:"):
            domains.append(part[2:].strip().lower())
        elif part.startswith("s:"):
            important.append(part[2:].strip())
        else:
            nums = _parse_indices(part, len(ranked))
            for n in nums:
                sender = ranked[n - 1][0]
                if sender:
                    important.append(sender)
    return sorted(set(important)), sorted(set(domains))


def run_mail_supervised(task: str) -> None:
    _print_header("MAIL: Supervised mailbox review")
    print("This mode will ask questions and only propose actions. No changes are made automatically.")

    provider = "yahoo"
    if "gmail" in task.lower():
        print("[MAIL] Gmail support is not configured yet. Only Yahoo is available right now.")
        return

    try:
        folders = yahoo_mail.list_folders()
    except Exception as exc:
        print(f"[MAIL] Failed to list folders: {exc}")
        print("[MAIL] Tip: run `Cred: yahoo_imap` with your app password.")
        return

    _print_header("Folders")
    for i, name in enumerate(folders, 1):
        print(f"  {i:>2}. {name}")

    scan_all = _prompt("Scan all folders? (y/n)", "y").lower().startswith("y")
    if scan_all:
        selected = folders
    else:
        raw = _prompt("Folder numbers to scan (e.g., 1,3,5)", "")
        picks = _parse_indices(raw, len(folders))
        selected = [folders[i - 1] for i in picks] if picks else ["INBOX"]

    full_scan = _prompt("Scan entire folders? (y/n)", "y").lower().startswith("y")
    per_folder_limit = None if full_scan else _prompt_int("How many most recent messages per folder", 200)

    senders = Counter()
    domains = Counter()
    message_headers: List[Dict[str, str]] = []

    def _progress(folder: str, idx: int, total: int) -> None:
        print(f"[MAIL] Scanning {folder}: {idx}/{total}")

    _print_header("Scanning")
    for folder in selected:
        try:
            headers = yahoo_mail.iter_headers(folder=folder, limit=per_folder_limit, progress_cb=_progress)
            message_headers.extend(headers)
            for h in headers:
                sender = h.get("from", "")
                if sender:
                    senders[sender] += 1
                    dom = _sender_domain(sender)
                    if dom:
                        domains[dom] += 1
        except Exception as exc:
            print(f"[MAIL] Failed to scan {folder}: {exc}")

    if not message_headers:
        print("[MAIL] No messages found in selected folders.")
        return

    _print_header("Top senders (most → least)")
    ranked_senders = senders.most_common()
    ranked_domains = domains.most_common()

    print(f"{'Rank':>4}  {'Count':>5}  Sender")
    for idx, (sender, count) in enumerate(_summarize_counts(ranked_senders, 25), 1):
        print(f"{idx:>4}  {count:>5}  {_format_sender(sender)}")

    _print_header("Top sender domains")
    print(f"{'Rank':>4}  {'Count':>5}  Domain")
    for idx, (dom, count) in enumerate(_summarize_counts(ranked_domains, 20), 1):
        print(f"{idx:>4}  {count:>5}  {dom}")

    _print_header("Mark important senders / spam")
    print("You can pick by rank number, or specify:")
    print("  d:domain.com  (domain)")
    print("  s:sender@example.com  (exact sender)")

    important_raw = _prompt("Important senders (optional)", "")
    important_senders, important_domains = _parse_sender_selection(important_raw, ranked_senders)

    spam_raw = _prompt("Spam senders (optional)", "")
    spam_senders, spam_domains = _parse_sender_selection(spam_raw, ranked_senders)

    _print_header("Folder health check")
    try:
        counts = yahoo_mail.folder_counts(selected)
    except Exception:
        counts = {name: 0 for name in selected}
    for name in selected:
        print(f"  - {name}: {counts.get(name, 0)} messages")

    folder_notes: Dict[str, str] = {}
    for name in selected:
        note = _prompt(f"Notes for folder '{name}' (keep/rename/empty?)", "")
        if note:
            folder_notes[name] = note

    _print_header("Rules cleanup")
    print("You said your existing rules/filters are wrong and should be removed.")
    remove_rules = _prompt("Do you want me to open Yahoo Mail settings so we can remove all rules now? (y/n)", "y")
    if remove_rules.lower().startswith("y"):
        print("\n[MAIL] Manual steps (we can automate later):")
        print("  1) Open Yahoo Mail")
        print("  2) Click Settings (gear) > More Settings")
        print("  3) Open Filters (or Rules)")
        print("  4) Delete each filter/rule")
        print("\n[MAIL] If you want automation, run: Learn: delete yahoo rules")

    suggestions = []
    for sender in spam_senders:
        suggestions.append(f"Mark sender as spam: {sender}")
    for dom in spam_domains:
        suggestions.append(f"Mark domain as spam: {dom}")
    for sender in important_senders:
        suggestions.append(f"Whitelist sender: {sender}")
    for dom in important_domains:
        suggestions.append(f"Whitelist domain: {dom}")

    _print_header("Proposed actions / rules (draft)")
    if suggestions:
        for s in suggestions:
            print(f"  - {s}")
    else:
        print("  (none yet)")

    # Store preferences to memory
    store = _open_memory_store()
    payload = {
        "provider": provider,
        "task": task,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "folders_scanned": selected,
        "scan_limit": per_folder_limit,
        "important_senders": important_senders,
        "important_domains": important_domains,
        "spam_senders": spam_senders,
        "spam_domains": spam_domains,
        "folder_notes": folder_notes,
        "suggestions": suggestions,
        "top_domains": domains.most_common(10),
        "top_senders": senders.most_common(10),
        "remove_rules_requested": remove_rules.lower().startswith("y"),
    }
    rec_id = store.upsert(
        kind="user_info",
        key=f"mail_preferences:{provider}",
        content=json.dumps(payload, ensure_ascii=False),
        metadata={"source": "mail_supervised"},
    )
    store.close()

    print(f"\n[MAIL] Saved your preferences to memory (id={rec_id}).")
    print("[MAIL] When you’re ready, I can help turn these suggestions into Yahoo rules.")
