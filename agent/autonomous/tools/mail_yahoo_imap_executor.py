from __future__ import annotations

import argparse
import imaplib
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from agent.memory.procedures.mail_yahoo import load_procedure, MoveRule

DEFAULT_HOST = "imap.mail.yahoo.com"
DEFAULT_PORT = 993
DEFAULT_SOURCE = "INBOX"


def _decode_bytes(value):
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return str(value)


def _quote_mailbox(name: str) -> str:
    if name.startswith('"') and name.endswith('"') and len(name) >= 2:
        name = name[1:-1]
    name = name.replace("\\", "\\\\").replace('"', '\\"')
    return f"\"{name}\""


def list_folders(imap: imaplib.IMAP4_SSL) -> List[str]:
    typ, data = imap.list()
    if typ != "OK":
        raise RuntimeError(f"LIST failed: {typ} {data}")
    folders: List[str] = []
    for line in data:
        if not line:
            continue
        b = line if isinstance(line, (bytes, bytearray)) else str(line).encode()
        m = re.search(rb'"([^"]+)"\s*$', b)
        if m:
            folders.append(m.group(1).decode(errors="replace"))
        else:
            folders.append(_decode_bytes(b).split()[-1].strip('"'))
    return folders


def folder_exists(folders: List[str], name: str) -> bool:
    return any(f == name for f in folders)


def ensure_folder(
    imap: imaplib.IMAP4_SSL, name: str, *, execute: bool, report_lines: List[str]
) -> bool:
    folders = list_folders(imap)
    if folder_exists(folders, name):
        print(f"[OK] Folder exists: {name}")
        report_lines.append(f"- folder_exists: {name}")
        return True
    print(f"[PLAN] Create folder: {name}")
    report_lines.append(f"- create_folder: {name}")
    if not execute:
        print("[DRY] Not creating (dry-run).")
        return False
    typ, data = imap.create(_quote_mailbox(name))
    if typ != "OK":
        raise RuntimeError(f"CREATE failed for {name}: {typ} {data}")
    print(f"[OK] Created folder: {name}")
    return True


def _since_date(days: int) -> str:
    date_val = datetime.now(timezone.utc) - timedelta(days=days)
    return date_val.strftime("%d-%b-%Y")


def build_search_tokens(rule: MoveRule) -> List[List[str]]:
    base_tokens: List[str] = []
    if rule.unread_only:
        base_tokens.append("UNSEEN")
    if rule.newer_than_days:
        base_tokens.extend(["SINCE", _since_date(rule.newer_than_days)])

    from_terms = rule.from_contains or []
    subject_terms = rule.subject_contains or []
    combos: List[List[str]] = []

    if from_terms and subject_terms:
        for from_term in from_terms:
            for subject_term in subject_terms:
                tokens = list(base_tokens)
                tokens.extend(["FROM", f"\"{from_term}\""])
                tokens.extend(["SUBJECT", f"\"{subject_term}\""])
                combos.append(tokens)
    elif from_terms:
        for from_term in from_terms:
            tokens = list(base_tokens)
            tokens.extend(["FROM", f"\"{from_term}\""])
            combos.append(tokens)
    elif subject_terms:
        for subject_term in subject_terms:
            tokens = list(base_tokens)
            tokens.extend(["SUBJECT", f"\"{subject_term}\""])
            combos.append(tokens)
    else:
        combos.append(list(base_tokens))

    return combos


def search_uids(
    imap: imaplib.IMAP4_SSL, source_folder: str, criteria: List[str]
) -> List[str]:
    typ, _ = imap.select(_quote_mailbox(source_folder), readonly=True)
    if typ != "OK":
        raise RuntimeError(f"SELECT failed for {source_folder}: {typ}")
    tokens = criteria if criteria else ["ALL"]
    typ, data = imap.uid("SEARCH", None, *tokens)
    if typ != "OK":
        raise RuntimeError(f"SEARCH failed: {typ} {data}")
    raw = data[0] if data else b""
    if isinstance(raw, bytes):
        raw = raw.decode(errors="replace")
    return [uid for uid in raw.split() if uid.strip()]


def move_uid(
    imap: imaplib.IMAP4_SSL, source_folder: str, uid: str, dest_folder: str
) -> Tuple[bool, str]:
    typ, _ = imap.select(_quote_mailbox(source_folder), readonly=False)
    if typ != "OK":
        return False, f"SELECT RW failed for {source_folder}: {typ}"
    typ, data = imap.uid("MOVE", uid, _quote_mailbox(dest_folder))
    if typ == "OK":
        return True, "MOVE"
    return False, f"MOVE failed: {typ} {data}"


def _load_creds() -> Tuple[str, str, str]:
    get_credential = None
    try:
        from agent.memory.credentials import get_credential as _get_credential

        get_credential = _get_credential
    except Exception:
        get_credential = None

    if get_credential is not None:
        try:
            creds = get_credential("yahoo_imap")
        except Exception:
            creds = None
        if creds:
            username = (creds.get("username") or "").strip()
            password = (creds.get("password") or "").strip()
            if password:
                password = password.replace(" ", "").replace("-", "")
            if username and password:
                return username, password, "credential_store"

    username = os.getenv("YAHOO_IMAP_USER", "").strip()
    password = os.getenv("YAHOO_IMAP_PASS", "").strip()
    if password:
        password = password.replace(" ", "").replace("-", "")
    if not username or not password:
        raise SystemExit(
            "Missing credentials. Provide saved 'yahoo_imap' credentials or set "
            "YAHOO_IMAP_USER and YAHOO_IMAP_PASS."
        )
    return username, password, "env"


def _run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"{stamp}_{os.urandom(4).hex()}"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _write_json(path: Path, payload: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_report(path: Path, lines: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _is_protected(name: str, protected: List[str]) -> bool:
    return name in protected


def main() -> int:
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Plan only (default)")
    mode.add_argument("--execute", action="store_true", help="Execute moves")
    ap.add_argument("--max-per-rule", type=int, default=None)
    ap.add_argument("--host", default=DEFAULT_HOST)
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--source", default=DEFAULT_SOURCE)
    args = ap.parse_args()

    execute = bool(args.execute)
    dry_run = not execute

    proc = load_procedure()
    run_id = _run_id()
    run_dir = _repo_root() / "runs" / run_id
    plan_path = run_dir / "mail_plan.json"
    report_path = run_dir / "mail_report.md"

    plan: Dict[str, object] = {
        "run_id": run_id,
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "execute": execute,
        "dry_run": dry_run,
        "max_per_rule": args.max_per_rule,
        "procedure": proc.model_dump(),
        "source_folder": args.source,
        "targets": [],
        "rules": [],
        "summary": {},
    }

    report_lines: List[str] = [
        "# Mail IMAP Executor Report",
        f"- time_utc: {datetime.now(timezone.utc).isoformat()}",
        f"- run_id: {run_id}",
        f"- execute: {execute}",
        f"- dry_run: {dry_run}",
        f"- source: {args.source}",
        "",
    ]

    success = True
    imap: Optional[imaplib.IMAP4_SSL] = None
    try:
        username, password, cred_source = _load_creds()
        report_lines.append(f"- credentials: {cred_source}")
        report_lines.append("")

        imap = imaplib.IMAP4_SSL(args.host, args.port)
        typ, _ = imap.login(username, password)
        if typ != "OK":
            raise RuntimeError("LOGIN failed")
        print("[OK] Logged in.")

        folders = list_folders(imap)
        print(f"[OK] Folders found: {len(folders)}")
        plan["folders"] = folders
        report_lines.append(f"## Folders ({len(folders)})")
        report_lines.extend([f"- {f}" for f in folders[:50]])
        report_lines.append("")

        protected = list(proc.protected_folders or [])
        plan["protected_folders"] = protected

        report_lines.append("## Targets")
        for target in proc.target_folders:
            item: Dict[str, object] = {
                "name": target,
                "protected": _is_protected(target, protected),
                "exists": folder_exists(folders, target),
            }
            if item["protected"]:
                print(f"[SKIP] Target folder is protected: {target}")
                report_lines.append(f"- protected_target: {target}")
                item["action"] = "skip_protected"
            else:
                created = False
                if not item["exists"]:
                    try:
                        created = ensure_folder(imap, target, execute=execute, report_lines=report_lines)
                    except Exception as exc:
                        success = False
                        print(f"[ERR] Failed to create folder {target}: {exc}")
                        report_lines.append(f"- create_failed: {target} error={exc}")
                item["created"] = created
                item["action"] = "ensure"
            plan["targets"].append(item)
        report_lines.append("")

        report_lines.append("## Rules")
        moved_total = 0
        matches_total = 0
        for rule in proc.rules:
            max_to_move = rule.max_messages
            if args.max_per_rule is not None:
                max_to_move = min(max_to_move, max(0, args.max_per_rule))
            rule_entry: Dict[str, object] = {
                "name": rule.name,
                "to_folder": rule.to_folder,
                "source_folder": args.source,
                "max_messages": rule.max_messages,
                "max_per_rule": args.max_per_rule,
                "planned_limit": max_to_move,
                "from_contains": rule.from_contains,
                "subject_contains": rule.subject_contains,
                "unread_only": rule.unread_only,
                "newer_than_days": rule.newer_than_days,
                "queries": [],
            }

            if _is_protected(rule.to_folder, protected):
                print(f"[SKIP] Rule '{rule.name}' targets protected folder: {rule.to_folder}")
                report_lines.append(f"- rule_skip_protected_target: {rule.name} -> {rule.to_folder}")
                rule_entry["status"] = "skip_protected_target"
                plan["rules"].append(rule_entry)
                continue

            if _is_protected(args.source, protected):
                print(f"[SKIP] Source folder is protected: {args.source}")
                report_lines.append(f"- rule_skip_protected_source: {rule.name} source={args.source}")
                rule_entry["status"] = "skip_protected_source"
                plan["rules"].append(rule_entry)
                continue

            combos = build_search_tokens(rule)
            rule_entry["queries"] = combos

            all_uids: List[str] = []
            seen: Dict[str, bool] = {}
            try:
                for tokens in combos:
                    print(f"[OK] Rule '{rule.name}' search: {tokens or ['ALL']}")
                    uids = search_uids(imap, args.source, tokens)
                    for uid in uids:
                        if uid not in seen:
                            seen[uid] = True
                            all_uids.append(uid)
            except Exception as exc:
                success = False
                print(f"[ERR] Rule '{rule.name}' search failed: {exc}")
                report_lines.append(f"- rule_search_failed: {rule.name} error={exc}")
                rule_entry["status"] = "search_failed"
                plan["rules"].append(rule_entry)
                continue

            matches_total += len(all_uids)
            planned_uids = all_uids[: max(0, max_to_move)]
            rule_entry["match_count"] = len(all_uids)
            rule_entry["planned_uids"] = planned_uids
            rule_entry["status"] = "planned"

            report_lines.append(f"- rule: {rule.name} matches={len(all_uids)} planned={len(planned_uids)}")

            if dry_run:
                print(f"[DRY] Rule '{rule.name}' planned moves: {len(planned_uids)}")
                plan["rules"].append(rule_entry)
                continue

            moved = 0
            for uid in planned_uids:
                ok, method = move_uid(imap, args.source, uid, rule.to_folder)
                if ok:
                    moved += 1
                    moved_total += 1
                    print(f"[OK] Moved UID {uid} -> {rule.to_folder} via {method}")
                    report_lines.append(f"- moved: rule={rule.name} uid={uid} method={method}")
                else:
                    success = False
                    print(f"[ERR] Failed to move UID {uid}: {method}")
                    report_lines.append(f"- move_failed: rule={rule.name} uid={uid} error={method}")

            rule_entry["moved"] = moved
            plan["rules"].append(rule_entry)

        plan["summary"] = {
            "rules_total": len(proc.rules),
            "matches_total": matches_total,
            "moved_total": moved_total,
        }
        report_lines.append("")
        report_lines.append("## Summary")
        report_lines.append(f"- rules_total: {len(proc.rules)}")
        report_lines.append(f"- matches_total: {matches_total}")
        report_lines.append(f"- moved_total: {moved_total}")

        _write_json(plan_path, plan)
        _write_report(report_path, report_lines)
        print(f"[OK] Wrote plan: {plan_path}")
        print(f"[OK] Wrote report: {report_path}")
        return 0 if success else 1
    except Exception as exc:
        success = False
        report_lines.append(f"- error: {exc}")
        try:
            _write_json(plan_path, plan)
            _write_report(report_path, report_lines)
        except Exception:
            pass
        print(f"[ERR] {exc}")
        return 1
    finally:
        if imap is not None:
            try:
                imap.logout()
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
