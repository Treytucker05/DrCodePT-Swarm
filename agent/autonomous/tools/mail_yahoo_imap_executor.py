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


def _load_plan(path: Path) -> Dict:
    if not path.is_file():
        raise FileNotFoundError(f"Plan file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Plan only (default)")
    mode.add_argument("--execute", action="store_true", help="Execute moves")
    mode.add_argument(
        "--scan-all-folders",
        action="store_true",
        help="Scan all folders for rule matches (no moves)",
    )
    ap.add_argument(
        "--no-create-folders",
        action="store_true",
        help="Do not create missing target folders",
    )
    ap.add_argument(
        "--plan-path",
        help="Execute using a specific dry-run plan file",
    )
    ap.add_argument("--max-per-rule", type=int, default=None)
    ap.add_argument("--host", default=DEFAULT_HOST)
    ap.add_argument("--port", default=DEFAULT_PORT)
    ap.add_argument("--source", default=DEFAULT_SOURCE)
    args = ap.parse_args()

    scan_mode = bool(args.scan_all_folders)
    execute = bool(args.execute) and not scan_mode
    dry_run = not execute
    plan_path_arg = Path(args.plan_path).resolve() if args.plan_path else None

    proc = load_procedure()
    run_id = _run_id()
    run_dir = _repo_root() / "runs" / run_id
    plan_path = run_dir / "mail_plan.json"
    report_path = run_dir / "mail_report.md"
    scan_path = run_dir / "mail_scan.json"

    plan: Dict[str, object] = {
        "run_id": run_id,
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "execute": execute,
        "dry_run": dry_run,
        "scan_all_folders": scan_mode,
        "no_create_folders": bool(args.no_create_folders),
        "plan_path": str(plan_path_arg) if plan_path_arg else None,
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
        f"- scan_all_folders: {scan_mode}",
        f"- no_create_folders: {bool(args.no_create_folders)}",
        f"- plan_path: {str(plan_path_arg) if plan_path_arg else ''}",
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

        if scan_mode:
            scan_results: Dict[str, Dict[str, int]] = {}
            scan_totals: Dict[str, int] = {}
            matches_total = 0

            report_lines.append("## Rules")
            for rule in proc.rules:
                combos = build_search_tokens(rule)
                rule_counts: Dict[str, int] = {}
                rule_total = 0
                for folder in folders:
                    try:
                        seen: Dict[str, bool] = {}
                        for tokens in combos:
                            uids = search_uids(imap, folder, tokens)
                            for uid in uids:
                                if uid not in seen:
                                    seen[uid] = True
                        count = len(seen)
                    except Exception as exc:
                        success = False
                        print(f"[ERR] Rule '{rule.name}' scan failed in {folder}: {exc}")
                        report_lines.append(
                            f"- rule_scan_failed: {rule.name} folder={folder} error={exc}"
                        )
                        continue

                    if count > 0:
                        print(f"[SCAN] Rule '{rule.name}' folder '{folder}' matches={count}")
                        rule_counts[folder] = count
                        rule_total += count

                scan_results[rule.name] = rule_counts
                scan_totals[rule.name] = rule_total
                matches_total += rule_total
                report_lines.append(
                    f"- rule: {rule.name} matched_total={rule_total} moved_total=0"
                )

            report_lines.append("")
            report_lines.append("## Summary")
            report_lines.append(f"- rules_total: {len(proc.rules)}")
            report_lines.append(f"- matches_total: {matches_total}")
            report_lines.append("- moved_total: 0")

            scan_payload = {
                "run_id": run_id,
                "time_utc": datetime.now(timezone.utc).isoformat(),
                "scan_all_folders": True,
                "rules": scan_results,
                "totals": {
                    "rules_total": len(proc.rules),
                    "matches_total": matches_total,
                    "by_rule": scan_totals,
                },
            }
            _write_json(scan_path, scan_payload)
            _write_report(report_path, report_lines)
            print(f"[OK] Wrote scan: {scan_path}")
            print(f"[OK] Wrote report: {report_path}")
            return 0 if success else 1

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
                    if args.no_create_folders:
                        print(f"[SKIP] Target missing and folder creation disabled: {target}")
                        report_lines.append(f"- missing_target_no_create: {target}")
                        item["action"] = "missing_no_create"
                    else:
                        try:
                            created = ensure_folder(imap, target, execute=execute, report_lines=report_lines)
                        except Exception as exc:
                            success = False
                            print(f"[ERR] Failed to create folder {target}: {exc}")
                            report_lines.append(f"- create_failed: {target} error={exc}")
                    item["created"] = created
                else:
                    item["created"] = False
                    item["action"] = "ensure"
            plan["targets"].append(item)
        report_lines.append("")

        report_lines.append("## Rules")
        moved_total = 0
        matches_total = 0
        plan_rules: Dict[str, Dict[str, object]] = {}
        if execute and plan_path_arg:
            plan_data = _load_plan(plan_path_arg)
            for entry in plan_data.get("rules") or []:
                name = entry.get("name")
                if isinstance(name, str):
                    plan_rules[name] = entry

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
                "planned_moves": [],
            }

            if _is_protected(rule.to_folder, protected):
                print(f"[SKIP] Rule '{rule.name}' targets protected folder: {rule.to_folder}")
                report_lines.append(f"- rule_skip_protected_target: {rule.name} -> {rule.to_folder}")
                rule_entry["status"] = "skip_protected_target"
                plan["rules"].append(rule_entry)
                continue

            if args.no_create_folders and not folder_exists(folders, rule.to_folder):
                success = False
                print(
                    f"[ERR] Rule '{rule.name}' target missing and folder creation disabled: {rule.to_folder}"
                )
                report_lines.append(
                    f"- rule_missing_target_no_create: {rule.name} -> {rule.to_folder}"
                )
                rule_entry["status"] = "missing_target_no_create"
                rule_entry["planned_moves"] = []
                plan["rules"].append(rule_entry)
                continue

            combos = build_search_tokens(rule)
            rule_entry["queries"] = combos

            planned_moves: List[Dict[str, str]] = []
            searched_folders: List[str] = []
            match_count = 0

            if execute and plan_path_arg and rule.name in plan_rules:
                planned_entry = plan_rules[rule.name]
                planned_moves = list(planned_entry.get("planned_moves") or [])
                if not planned_moves:
                    planned_uids = planned_entry.get("planned_uids") or []
                    source_folder = planned_entry.get("source_folder") or args.source
                    planned_moves = [
                        {"source_folder": source_folder, "uid": uid}
                        for uid in planned_uids
                        if isinstance(uid, str)
                    ]
                match_count = planned_entry.get("match_count") or len(planned_moves)
                searched_folders = list(planned_entry.get("searched_folders") or [])
            else:
                seen_pairs: Dict[Tuple[str, str], bool] = {}
                folders_to_search = getattr(rule, "search_folders", None) or [args.source]
                for folder in folders_to_search:
                    if folder == rule.to_folder:
                        print(f"[SKIP] Rule '{rule.name}' source == destination: {folder}")
                        continue
                    if _is_protected(folder, protected):
                        print(f"[SKIP] Rule '{rule.name}' source folder protected: {folder}")
                        report_lines.append(f"- rule_skip_protected_source: {rule.name} source={folder}")
                        continue
                    searched_folders.append(folder)
                    try:
                        for tokens in combos:
                            print(f"[OK] Rule '{rule.name}' search in {folder}: {tokens or ['ALL']}")
                            uids = search_uids(imap, folder, tokens)
                            for uid in uids:
                                pair = (folder, uid)
                                if pair in seen_pairs:
                                    continue
                                seen_pairs[pair] = True
                                match_count += 1
                                if len(planned_moves) < max_to_move:
                                    planned_moves.append({"source_folder": folder, "uid": uid})
                    except Exception as exc:
                        success = False
                        print(f"[ERR] Rule '{rule.name}' search failed in {folder}: {exc}")
                        report_lines.append(f"- rule_search_failed: {rule.name} folder={folder} error={exc}")
                        continue
                    if len(planned_moves) >= max_to_move:
                        break

            matches_total += match_count
            rule_entry["match_count"] = match_count
            rule_entry["planned_uids"] = [m["uid"] for m in planned_moves]
            rule_entry["planned_moves"] = planned_moves
            rule_entry["searched_folders"] = searched_folders
            rule_entry["status"] = "planned"

            if dry_run:
                print(
                    f"[DRY] Rule '{rule.name}' planned moves: {len(planned_moves)} (searched: {', '.join(searched_folders)})"
                )
                report_lines.append(
                    f"- rule: {rule.name} matched_total={match_count} planned={len(planned_moves)} attempted=0 moved_total=0"
                )
                plan["rules"].append(rule_entry)
                continue

            if args.max_per_rule is not None:
                max_to_move = min(len(planned_moves), max(0, args.max_per_rule))
            else:
                max_to_move = len(planned_moves)
            to_execute = planned_moves[:max_to_move]
            attempted = 0
            moved = 0
            for move in to_execute:
                attempted += 1
                ok, method = move_uid(imap, move["source_folder"], move["uid"], rule.to_folder)
                if ok:
                    moved += 1
                    moved_total += 1
                    print(
                        f"[OK] Moved UID {move['uid']} from {move['source_folder']} -> {rule.to_folder} via {method}"
                    )
                    report_lines.append(
                        f"- moved: rule={rule.name} source={move['source_folder']} uid={move['uid']} method={method}"
                    )
                else:
                    success = False
                    print(f"[ERR] Failed to move UID {move['uid']}: {method}")
                    report_lines.append(
                        f"- move_failed: rule={rule.name} source={move['source_folder']} uid={move['uid']} error={method}"
                    )

            report_lines.append(
                f"- rule: {rule.name} matched_total={match_count} planned={len(planned_moves)} attempted={attempted} moved_total={moved}"
            )
            rule_entry["attempted"] = attempted
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
