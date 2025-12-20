from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
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


def run_mail_supervised(task: str) -> None:
    print("\n[MAIL] Supervised mailbox review (collaborative).")
    print("[MAIL] This mode will ask questions and only propose actions.")

    provider = "yahoo"
    if "gmail" in task.lower():
        print("[MAIL] Gmail support is not configured yet. Only Yahoo is available right now.")
        return

    limit = _prompt_int("How many recent messages should I scan", 25)

    try:
        messages = yahoo_mail.list_messages(limit=limit, folder="INBOX")
    except Exception as exc:
        print(f"[MAIL] Failed to read inbox: {exc}")
        print("[MAIL] Tip: run `Cred: yahoo_imap` with your app password.")
        return

    if not messages:
        print("[MAIL] No messages found.")
        return

    print(f"\n[MAIL] Latest {len(messages)} inbox headers:")
    for i, msg in enumerate(messages, 1):
        print(f"  {i:>2}. {msg.get('date','')} | {msg.get('from','')} | {msg.get('subject','')}")

    domains = Counter(_sender_domain(m.get("from", "")) for m in messages if m.get("from"))
    senders = Counter(m.get("from", "") for m in messages if m.get("from"))

    print("\n[MAIL] Top sender domains:")
    for dom, count in domains.most_common(8):
        if dom:
            print(f"  - {dom}: {count}")

    print("\n[MAIL] Top senders:")
    for sender, count in senders.most_common(8):
        if sender:
            print(f"  - {sender}: {count}")

    to_summarize = _prompt("Message numbers to summarize (e.g., 1,3,5 or 2-4). Leave blank to skip", "")
    picks = _parse_indices(to_summarize, len(messages))

    summaries: Dict[int, str] = {}
    if picks:
        print("\n[MAIL] Fetching message previews...")
        for idx in picks:
            msg = messages[idx - 1]
            try:
                full = yahoo_mail.read_message(msg["uid"], folder="INBOX")
                body = (full.get("body") or "").strip().replace("\n", " ")
                summaries[idx] = body[:400]
            except Exception as exc:
                summaries[idx] = f"[Failed to read message: {exc}]"

        for idx, preview in summaries.items():
            subj = messages[idx - 1].get("subject", "")
            print(f"\n[MAIL] #{idx} — {subj}\n{preview}")

    spam_raw = _prompt("Which message numbers look like spam (optional)", "")
    spam_picks = _parse_indices(spam_raw, len(messages))

    keep_raw = _prompt("Which message numbers are important/keep (optional)", "")
    keep_picks = _parse_indices(keep_raw, len(messages))

    categories: Dict[str, List[int]] = defaultdict(list)
    print("\n[MAIL] Categorize messages (optional).")
    print("Example: newsletters: 1,4,5    or receipts: 2-3")
    while True:
        line = _prompt("Category assignment (blank to finish)", "")
        if not line:
            break
        if ":" not in line:
            print("[MAIL] Format should be: category: 1,2,3")
            continue
        name, picks_raw = line.split(":", 1)
        name = name.strip()
        picks = _parse_indices(picks_raw, len(messages))
        if name and picks:
            categories[name].extend(picks)

    # Build rule suggestions from spam/categories
    suggestions = []
    if spam_picks:
        for idx in spam_picks:
            sender = messages[idx - 1].get("from", "")
            if sender:
                suggestions.append(f"Mark sender as spam: {sender}")
    for cat, idxs in categories.items():
        for idx in sorted(set(idxs)):
            sender = messages[idx - 1].get("from", "")
            if sender:
                suggestions.append(f"Rule: if sender is {sender} -> move to folder '{cat}'")

    print("\n[MAIL] Proposed actions / rules:")
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
        "scan_limit": limit,
        "spam_indices": spam_picks,
        "keep_indices": keep_picks,
        "categories": dict(categories),
        "suggestions": suggestions,
        "top_domains": domains.most_common(10),
        "top_senders": senders.most_common(10),
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

