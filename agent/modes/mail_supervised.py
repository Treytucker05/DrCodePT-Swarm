from __future__ import annotations

import json
import os
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from agent.autonomous.memory.sqlite_store import SqliteMemoryStore
from agent.integrations import yahoo_mail
from agent.memory.credentials import get_credential


SYSTEM_FOLDERS = {
    "INBOX",
    "Sent",
    "Sent Mail",
    "Draft",
    "Drafts",
    "Trash",
    "Spam",
    "Archive",
}


AUTO_CATEGORY_FOLDERS = {
    "from_myself": ["From Myself", "Myself", "Self"],
    "work_usertesting": ["Work/UserTesting", "Work - UserTesting", "UserTesting"],
    "work_github": ["Work/GitHub", "Work - GitHub", "GitHub"],
    "finance": ["Finance", "Bills", "Payments"],
    "shopping": ["Shopping", "Shopping/Online", "Purchases"],
    "deliveries": ["Deliveries", "Shopping/Deliveries"],
    "newsletters": ["Newsletters", "Subscriptions/Newsletters", "Subscriptions"],
    "social": ["Social", "Community", "Social/Community"],
    "subscriptions": ["Subscriptions", "Entertainment", "Streaming"],
    "fitness": ["Fitness", "Health/Fitness", "Health"],
    "childcare": ["Childcare", "Family/Childcare", "Kids"],
    "security": ["Security", "Important/Security", "Important"],
    "sports": ["Sports", "Sports/Fantasy"],
    "personal": ["Personal", "Personal/Family"],
}


AUTO_DOMAIN_RULES = {
    "usertesting.com": "work_usertesting",
    "github.com": "work_github",
    "paypal.com": "finance",
    "venmo.com": "finance",
    "email.rocketmoney.com": "finance",
    "m.purchasingpower.com": "finance",
    "amazon.com": "shopping",
    "woot.com": "shopping",
    "crocs-email.com": "shopping",
    "tryautobrush.com": "shopping",
    "irobot.com": "shopping",
    "email.informeddelivery.usps.com": "deliveries",
    "mail.beehiiv.com": "newsletters",
    "substack.com": "newsletters",
    "patreon.com": "social",
    "rumble.com": "social",
    "contact@email.paramountplus.com": "subscriptions",
    "paramountplus.com": "subscriptions",
    "online.procaresoftware.com": "childcare",
    "repfitness.com": "fitness",
    "performbetter.com": "fitness",
    "e.performbetter.com": "fitness",
    "muscleandmotion.com": "fitness",
    "brookbushinstitute.com": "fitness",
    "altis.world": "fitness",
    "accounts.google.com": "security",
    "email.apple.com": "security",
}


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


def _leaf_name(name: str, delimiter: str) -> str:
    if not name:
        return name
    normalized = name.replace("/", delimiter)
    return normalized.split(delimiter)[-1]


def _normalize_path(path: str, delimiter: str) -> str:
    if not path:
        return path
    path = path.replace("/", delimiter)
    if delimiter != "/":
        path = path.replace("\\", delimiter)
    return path


def _sender_domain(sender: str) -> str:
    if not sender:
        return ""
    m = re.search(r"@([A-Za-z0-9._-]+\.[A-Za-z]{2,})", sender)
    return m.group(1).lower() if m else ""


def _open_memory_store() -> SqliteMemoryStore:
    root = Path(__file__).resolve().parents[1]
    memory_path = os.getenv("AGENT_MEMORY_DB") or str(root / "memory" / "autonomous_memory.sqlite3")
    return SqliteMemoryStore(Path(memory_path))


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


def _guess_self_emails() -> List[str]:
    creds = get_credential("yahoo_imap") or {}
    username = (creds.get("username") or "").strip()
    if username:
        return [username.lower()]
    return []


def _choose_folder_name(key: str, folders: List[str]) -> str:
    candidates = AUTO_CATEGORY_FOLDERS.get(key, [])
    for cand in candidates:
        for existing in folders:
            if existing.lower() == cand.lower():
                return existing
    return candidates[0] if candidates else "Review"


def _auto_classify(sender: str, domain: str, self_emails: List[str]) -> Tuple[str, str, str]:
    sender_l = (sender or "").lower()
    domain_l = (domain or "").lower()
    for self_email in self_emails:
        if self_email and self_email in sender_l:
            return "from_myself", "high", "matches your email"

    if domain_l in AUTO_DOMAIN_RULES:
        return AUTO_DOMAIN_RULES[domain_l], "high", f"domain match: {domain_l}"

    if "newsletter" in sender_l or "news" in sender_l:
        return "newsletters", "medium", "sender contains newsletter/news"
    if "receipt" in sender_l or "invoice" in sender_l:
        return "finance", "medium", "sender looks like receipts"
    if "shipping" in sender_l or "delivery" in sender_l:
        return "deliveries", "medium", "sender looks like deliveries"
    if "security" in sender_l or "account" in sender_l:
        return "security", "medium", "sender looks like account/security"
    if "fitness" in sender_l or "workout" in sender_l:
        return "fitness", "medium", "sender looks like fitness"

    return "personal", "low", "no strong match"


def run_mail_supervised(task: str) -> None:
    _print_header("MAIL: Interactive Organization Assistant")
    print("I'll help you organize your mailbox. Let's start by understanding what you want to do.")
    print()

    provider = "yahoo"
    if "gmail" in task.lower():
        print("[MAIL] Gmail support is not configured yet. Only Yahoo is available right now.")
        return

    try:
        folders, delimiter = yahoo_mail.list_folders_with_delimiter()
    except Exception as exc:
        print(f"[MAIL] Failed to list folders: {exc}")
        print("[MAIL] Tip: run `Cred: yahoo_imap` with your app password.")
        return

    _print_header("Your Current Folders")
    for i, name in enumerate(folders, 1):
        print(f"  {i:>2}. {name}")

    print()
    print("What would you like to do?")
    print("  1) Get a quick overview (scan recent messages)")
    print("  2) Deep dive into specific folders")
    print("  3) Plan a folder reorganization strategy")
    print("  4) Find and clean up spam/unwanted senders")
    print("  5) Custom - tell me what you need")
    print()

    choice = _prompt("Choose an option (1-5)", "1").strip()

    if choice == "3":
        print()
        print("[MAIL] Let's plan your folder organization strategy.")
        print()
        print("Current folder structure:")
        for name in folders:
            if name not in SYSTEM_FOLDERS:
                print(f"  - {name}")
        print()

        goal = _prompt("What's your main goal? (e.g., 'separate work from personal', 'organize by topic')", "")
        if goal:
            print(f"\n[MAIL] Goal: {goal}")
            print("\nLet me suggest some strategies:")
            print("  • Create top-level categories (Work, Personal, Finance, etc.)")
            print("  • Use subfolders for specific topics")
            print("  • Set up rules to auto-file incoming mail")
            print()

        strategy = _prompt("Do you want to: (a) scan first to see what you have, (b) create folders now, (c) both", "a").lower()

        if strategy.startswith("b") or strategy.startswith("c"):
            print("\n[MAIL] Let's create some folders.")
            while True:
                new_folder = _prompt("New folder name (or 'done' to finish)", "").strip()
                if not new_folder or new_folder.lower() == "done":
                    break
                try:
                    yahoo_mail.create_folder(new_folder)
                    folders.append(new_folder)
                    print(f"[MAIL] ✓ Created folder: {new_folder}")
                except Exception as exc:
                    print(f"[MAIL] Failed to create {new_folder}: {exc}")

            if strategy.startswith("b"):
                print("\n[MAIL] Folders created! Run this again when you're ready to organize messages.")
                return

        print("\n[MAIL] Now let's scan to see what you have...")
        choice = "1"

    elif choice == "4":
        print()
        print("[MAIL] Let's find spam and unwanted senders.")
        scan_target = _prompt("Which folder to scan? (default: INBOX)", "INBOX").strip()
        if scan_target not in folders:
            scan_target = "INBOX"
        selected = [scan_target]
        per_folder_limit = _prompt_int("How many recent messages to check", 200)
        chunked_scan = False
        chunk_size = 0
        chunks_per_folder = 0

    elif choice == "5":
        print()
        custom_goal = _prompt("Tell me what you need help with", "")
        print(f"\n[MAIL] Got it: {custom_goal}")
        print("\nLet's start by scanning to understand your mailbox...")
        choice = "1"

    if choice in ["1", "2", "5"] or choice == "3":
        if choice == "2":
            print()
            print("[MAIL] Which folders do you want to focus on?")
            raw = _prompt("Folder numbers (e.g., 1,3,5) or 'all'", "")
            if raw.lower() == "all":
                selected = folders
            else:
                picks = _parse_indices(raw, len(folders))
                selected = [folders[i - 1] for i in picks] if picks else ["INBOX"]
        else:
            scan_all = _prompt("\nScan all folders? (y/n)", "n").lower().startswith("y")
            if scan_all:
                selected = folders
            else:
                raw = _prompt("Folder numbers to scan (e.g., 1,3,5) or just press Enter for INBOX", "")
                picks = _parse_indices(raw, len(folders))
                selected = [folders[i - 1] for i in picks] if picks else ["INBOX"]

        chunked_scan = _prompt("Scan in chunks from most recent? (y/n)", "y").lower().startswith("y")
        if chunked_scan:
            chunk_size = _prompt_int("Chunk size (messages per folder)", 200)
            chunks_per_folder = _prompt_int("How many chunks per folder this run", 1)
            per_folder_limit = None
        else:
            full_scan = _prompt("Scan entire folders? (y/n)", "n").lower().startswith("y")
            per_folder_limit = None if full_scan else _prompt_int("How many most recent messages per folder", 200)
            chunk_size = 0
            chunks_per_folder = 0

    senders = Counter()
    domains = Counter()
    message_headers: List[Dict[str, str]] = []
    scan_errors: List[Dict[str, str]] = []
    self_emails = _guess_self_emails()

    def _progress(folder: str, idx: int, total: int) -> None:
        print(f"[MAIL] Scanning {folder}: {idx}/{total}")

    def _chunk_progress(folder: str, idx: int, total: int) -> None:
        print(f"[MAIL] Scanning {folder} (chunk): {idx}/{total}")

    _print_header("Scanning")
    for folder in selected:
        try:
            if chunked_scan:
                ids = yahoo_mail.list_message_ids(folder)
                total_ids = len(ids)
                if total_ids == 0:
                    continue
                for chunk_idx in range(chunks_per_folder):
                    end = total_ids - (chunk_idx * chunk_size)
                    start = max(0, end - chunk_size)
                    if start >= end:
                        break
                    chunk_uids = ids[start:end]
                    print(
                        f"[MAIL] {folder}: chunk {chunk_idx + 1}/{chunks_per_folder} "
                        f"({start + 1}-{end} of {total_ids})"
                    )
                    headers = yahoo_mail.fetch_headers_by_uids(folder, chunk_uids, progress_cb=_chunk_progress)
                    message_headers.extend(headers)
                    for h in headers:
                        sender = h.get("from", "")
                        if sender:
                            senders[sender] += 1
                            dom = _sender_domain(sender)
                            if dom:
                                domains[dom] += 1
            else:
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
            scan_errors.append({"folder": folder, "error": str(exc)})

    if not message_headers:
        print("[MAIL] No messages found in selected folders.")
        return

    _print_header("Top senders (most to least)")
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
        counts_all = yahoo_mail.folder_counts(folders)
    except Exception:
        counts_all = {name: 0 for name in folders}
    for name in selected:
        print(f"  - {name}: {counts_all.get(name, 0)} messages")

    folder_notes: Dict[str, str] = {}
    for name in selected:
        note = _prompt(f"Notes for folder '{name}' (keep/rename/empty?)", "")
        if note:
            folder_notes[name] = note

    _print_header("Rules cleanup")
    print("You said your existing rules/filters are wrong and should be removed.")
    print("[MAIL] Yahoo doesn't expose filters via IMAP, so we must use the web UI to view/delete them.")
    remove_rules = _prompt("Do you want to handle rules cleanup now via the browser? (y/n)", "y")
    if remove_rules.lower().startswith("y"):
        print("\n[MAIL] Manual steps (we can automate with a playbook):")
        print("  1) Open Yahoo Mail")
        print("  2) Click Settings (gear) > More Settings")
        print("  3) Open Filters (or Rules)")
        print("  4) Review and delete each filter/rule")
        print("\n[MAIL] If you want automation, we can record a playbook: Learn: delete yahoo rules")

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

    _print_header("Auto-triage suggestions (draft)")
    auto_moves: List[Dict[str, str]] = []
    ranked_for_auto = _summarize_counts(ranked_senders, 25)
    for sender, count in ranked_for_auto:
        dom = _sender_domain(sender)
        key, confidence, reason = _auto_classify(sender, dom, self_emails)
        folder = _choose_folder_name(key, folders)
        auto_moves.append(
            {
                "type": "sender",
                "value": sender,
                "domain": dom,
                "count": str(count),
                "dest": folder,
                "confidence": confidence,
                "reason": reason,
            }
        )

    print(f"{'Rank':>4}  {'Count':>5}  {'Confidence':>10}  {'Destination':<24}  Sender")
    for idx, item in enumerate(auto_moves, 1):
        print(
            f"{idx:>4}  {item['count']:>5}  {item['confidence']:>10}  {item['dest']:<24}  {_format_sender(item['value'])}"
        )

    use_auto_raw = _prompt("Use auto-triage for high-confidence senders? (y/n)", "y")
    use_auto = use_auto_raw.lower().startswith("y")
    auto_apply_threshold = "high"

    execution_log: List[Dict[str, str]] = []
    execution_errors: List[Dict[str, str]] = []

    _print_header("Optional: apply changes now")
    apply_now = _prompt("Apply folder changes or message moves now? (y/n)", "n").lower().startswith("y")
    if apply_now:
        _print_header("Folder consolidation")
        print("You can group folders under parent categories or delete unused folders.")
        print("Use folder numbers from the list above.")

        raw_delete = _prompt("Delete folders (numbers, blank to skip)", "")
        delete_picks = _parse_indices(raw_delete, len(folders))
        delete_targets = [folders[i - 1] for i in delete_picks] if delete_picks else []
        safe_delete_targets = [f for f in delete_targets if f not in SYSTEM_FOLDERS]
        if delete_targets and not safe_delete_targets:
            print("[MAIL] Skipping deletion for system folders.")

        mapping_lines: List[str] = []
        while True:
            line = _prompt("Map folders (e.g., 1,2 -> Finance or 4 -> Finance/Taxes). Blank to finish", "")
            if not line:
                break
            mapping_lines.append(line)

        rename_actions: List[Tuple[str, str]] = []
        existing = set(folders)
        for line in mapping_lines:
            if "->" not in line:
                continue
            left, right = line.split("->", 1)
            picks = _parse_indices(left.strip(), len(folders))
            target = _normalize_path(right.strip(), delimiter)
            for idx in picks:
                old_name = folders[idx - 1]
                if old_name in SYSTEM_FOLDERS:
                    continue
                if not target:
                    continue
                if delimiter in target:
                    new_name = target
                else:
                    new_name = f"{target}{delimiter}{_leaf_name(old_name, delimiter)}"
                new_name = _normalize_path(new_name, delimiter)
                if new_name == old_name:
                    continue
                rename_actions.append((old_name, new_name))

        if safe_delete_targets:
            print("\n[MAIL] Delete folders:")
            for name in safe_delete_targets:
                print(f"  - {name} ({counts_all.get(name, 0)} messages)")
            confirm_delete = _prompt("Type DELETE to confirm", "")
            if confirm_delete.strip().upper() == "DELETE":
                for name in safe_delete_targets:
                    try:
                        yahoo_mail.delete_folder(name)
                        execution_log.append({"action": "delete_folder", "folder": name})
                        existing.discard(name)
                    except Exception as exc:
                        execution_errors.append({"action": "delete_folder", "folder": name, "error": str(exc)})
                        print(f"[MAIL] Failed to delete {name}: {exc}")
            else:
                print("[MAIL] Deletion skipped.")

        if rename_actions:
            print("\n[MAIL] Rename / move folders:")
            for old_name, new_name in rename_actions:
                print(f"  - {old_name} -> {new_name}")
            if _prompt("Proceed with these renames? (y/n)", "n").lower().startswith("y"):
                for old_name, new_name in rename_actions:
                    try:
                        # Ensure parent exists if needed
                        if delimiter in new_name:
                            parent = new_name.rsplit(delimiter, 1)[0]
                            if parent and parent not in existing:
                                yahoo_mail.create_folder(parent)
                                existing.add(parent)
                                execution_log.append({"action": "create_folder", "folder": parent})
                        yahoo_mail.rename_folder(old_name, new_name)
                        execution_log.append({"action": "rename_folder", "from": old_name, "to": new_name})
                        existing.discard(old_name)
                        existing.add(new_name)
                    except Exception as exc:
                        execution_errors.append(
                            {"action": "rename_folder", "from": old_name, "to": new_name, "error": str(exc)}
                        )
                        print(f"[MAIL] Failed to rename {old_name} -> {new_name}: {exc}")

        _print_header("Sender/domain moves")
        if spam_senders or spam_domains or important_senders or important_domains:
            do_moves = _prompt("Move messages by sender/domain now? (y/n)", "n").lower().startswith("y")
            if do_moves:
                spam_dest = _prompt("Spam destination folder", "Spam")
                important_dest = _prompt("Important destination folder", "Important")
                expunge = _prompt("Expunge (remove from source) after move? (y/n)", "n").lower().startswith("y")

                for dest in [spam_dest, important_dest]:
                    if dest and dest not in existing:
                        try:
                            yahoo_mail.create_folder(dest)
                            existing.add(dest)
                            execution_log.append({"action": "create_folder", "folder": dest})
                        except Exception as exc:
                            execution_errors.append({"action": "create_folder", "folder": dest, "error": str(exc)})
                            print(f"[MAIL] Failed to create folder {dest}: {exc}")

                for sender in spam_senders:
                    try:
                        moved = yahoo_mail.move_by_sender("INBOX", sender, spam_dest, expunge=expunge)
                        execution_log.append(
                            {"action": "move_by_sender", "sender": sender, "dest": spam_dest, "count": str(moved)}
                        )
                    except Exception as exc:
                        execution_errors.append(
                            {"action": "move_by_sender", "sender": sender, "dest": spam_dest, "error": str(exc)}
                        )
                        print(f"[MAIL] Failed to move sender {sender}: {exc}")

                for dom in spam_domains:
                    try:
                        moved = yahoo_mail.move_by_domain("INBOX", dom, spam_dest, expunge=expunge)
                        execution_log.append(
                            {"action": "move_by_domain", "domain": dom, "dest": spam_dest, "count": str(moved)}
                        )
                    except Exception as exc:
                        execution_errors.append(
                            {"action": "move_by_domain", "domain": dom, "dest": spam_dest, "error": str(exc)}
                        )
                        print(f"[MAIL] Failed to move domain {dom}: {exc}")

                for sender in important_senders:
                    try:
                        moved = yahoo_mail.move_by_sender("INBOX", sender, important_dest, expunge=expunge)
                        execution_log.append(
                            {
                                "action": "move_by_sender",
                                "sender": sender,
                                "dest": important_dest,
                                "count": str(moved),
                            }
                        )
                    except Exception as exc:
                        execution_errors.append(
                            {"action": "move_by_sender", "sender": sender, "dest": important_dest, "error": str(exc)}
                        )
                        print(f"[MAIL] Failed to move sender {sender}: {exc}")

                for dom in important_domains:
                    try:
                        moved = yahoo_mail.move_by_domain("INBOX", dom, important_dest, expunge=expunge)
                        execution_log.append(
                            {"action": "move_by_domain", "domain": dom, "dest": important_dest, "count": str(moved)}
                        )
                    except Exception as exc:
                        execution_errors.append(
                            {"action": "move_by_domain", "domain": dom, "dest": important_dest, "error": str(exc)}
                        )
                        print(f"[MAIL] Failed to move domain {dom}: {exc}")
        else:
            print("No senders/domains selected yet.")

        if use_auto:
            _print_header("Auto-triage moves")
            do_auto = _prompt("Apply auto-triage moves now? (y/n)", "n").lower().startswith("y")
            if do_auto:
                expunge = _prompt("Expunge (remove from source) after auto moves? (y/n)", "n").lower().startswith("y")
                for item in auto_moves:
                    if item["confidence"] != auto_apply_threshold:
                        continue
                    dest = item["dest"]
                    if dest and dest not in existing:
                        try:
                            yahoo_mail.create_folder(dest)
                            existing.add(dest)
                            execution_log.append({"action": "create_folder", "folder": dest})
                        except Exception as exc:
                            execution_errors.append({"action": "create_folder", "folder": dest, "error": str(exc)})
                            print(f"[MAIL] Failed to create folder {dest}: {exc}")
                            continue
                    try:
                        moved = yahoo_mail.move_by_sender("INBOX", item["value"], dest, expunge=expunge)
                        execution_log.append(
                            {
                                "action": "auto_move_sender",
                                "sender": item["value"],
                                "dest": dest,
                                "count": str(moved),
                            }
                        )
                    except Exception as exc:
                        execution_errors.append(
                            {"action": "auto_move_sender", "sender": item["value"], "dest": dest, "error": str(exc)}
                        )
                        print(f"[MAIL] Failed to move sender {item['value']}: {exc}")

        if execution_log:
            _print_header("Execution summary")
            for item in execution_log:
                print(f"  - {item}")
        if execution_errors:
            _print_header("Execution issues")
            for item in execution_errors:
                print(f"  - {item}")

    # Store preferences to memory
    store = _open_memory_store()
    payload = {
        "provider": provider,
        "task": task,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "folders_scanned": selected,
        "scan_limit": per_folder_limit,
        "chunked_scan": chunked_scan,
        "chunk_size": chunk_size,
        "chunks_per_folder": chunks_per_folder,
        "important_senders": important_senders,
        "important_domains": important_domains,
        "spam_senders": spam_senders,
        "spam_domains": spam_domains,
        "folder_notes": folder_notes,
        "suggestions": suggestions,
        "top_domains": domains.most_common(10),
        "top_senders": senders.most_common(10),
        "remove_rules_requested": remove_rules.lower().startswith("y"),
        "scan_errors": scan_errors,
        "execution_log": execution_log,
        "execution_errors": execution_errors,
        "auto_moves": auto_moves,
        "auto_apply_threshold": auto_apply_threshold,
        "auto_use_enabled": use_auto,
    }
    rec_id = store.upsert(
        kind="user_info",
        key=f"mail_preferences:{provider}",
        content=json.dumps(payload, ensure_ascii=False),
        metadata={"source": "mail_supervised"},
    )
    store.close()

    print(f"\n[MAIL] Saved your preferences to memory (id={rec_id}).")
    print("[MAIL] When you're ready, I can help turn these suggestions into Yahoo rules.")
