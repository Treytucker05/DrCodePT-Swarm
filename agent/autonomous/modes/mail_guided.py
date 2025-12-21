from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from agent.memory.procedures.mail_yahoo import load_procedure, save_procedure, MailProcedure

REPO_ROOT = Path(__file__).resolve().parents[3]
RUNS_DIR = REPO_ROOT / "runs"

RULE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "name": {"type": "string"},
        "to_folder": {"type": "string"},
        "from_contains": {"type": "array", "items": {"type": "string"}},
        "subject_contains": {"type": "array", "items": {"type": "string"}},
        "max_messages": {"type": "integer"},
        "newer_than_days": {"type": ["integer", "null"]},
        "unread_only": {"type": "boolean"},
    },
    "required": [
        "name",
        "to_folder",
        "from_contains",
        "subject_contains",
        "max_messages",
        "newer_than_days",
        "unread_only",
    ],
}

PROCEDURE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "version": {"type": "string"},
        "provider": {"type": "string"},
        "account_label": {"type": "string"},
        "target_folders": {"type": "array", "items": {"type": "string"}},
        "rules": {"type": "array", "items": RULE_SCHEMA},
        "protected_folders": {"type": "array", "items": {"type": "string"}},
        "last_updated_utc": {"type": "string"},
    },
    "required": [
        "version",
        "provider",
        "account_label",
        "target_folders",
        "rules",
        "protected_folders",
        "last_updated_utc",
    ],
}

QUESTIONER_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "questions": {"type": "array", "items": {"type": "string"}},
        "rationale": {"type": "string"},
    },
    "required": ["questions", "rationale"],
}

PLANNER_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "procedure": PROCEDURE_SCHEMA,
        "summary": {"type": "string"},
    },
    "required": ["procedure", "summary"],
}

CRITIC_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "summary": {"type": "string"},
        "suggestions": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["summary", "suggestions"],
}


def _write_schema(schema: Dict[str, Any]) -> Path:
    path = Path(tempfile.gettempdir()) / f"mail_guided_schema_{uuid4().hex}.json"
    path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    return path


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


def _run_codex_json(prompt: str, schema: Dict[str, Any], *, profile: str = "reason", timeout_seconds: Optional[int] = 60) -> Dict[str, Any]:
    codex_bin = (os.getenv("CODEX_BIN") or "codex").strip()
    model = (os.getenv("CODEX_MODEL") or "").strip()
    resolved = shutil.which(codex_bin) or codex_bin
    schema_path = _write_schema(schema)
    out_path = Path(tempfile.gettempdir()) / f"codex_last_message_{uuid4().hex}.json"

    codex_args = [
        "--profile",
        profile,
        "--dangerously-bypass-approvals-and-sandbox",
        "--search",
        "--disable",
        "rmcp_client",
        "--disable",
        "shell_tool",
        "exec",
        "--skip-git-repo-check",
        "--output-schema",
        str(schema_path),
        "--output-last-message",
        str(out_path),
    ]
    if resolved.lower().endswith(".ps1"):
        cmd = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            resolved,
            *codex_args,
        ]
    else:
        cmd = [resolved, *codex_args]

    if model:
        cmd.extend(["--model", model])

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"

    try:
        proc = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            env=env,
            timeout=timeout_seconds,
        )
    finally:
        try:
            schema_path.unlink(missing_ok=True)  # type: ignore[call-arg]
        except Exception:
            pass

    if proc.returncode != 0:
        stdout = (proc.stdout or "").strip()
        stderr = (proc.stderr or "").strip()
        raise RuntimeError(
            "codex exec failed. "
            f"stdout: {stdout[:300]} "
            f"stderr: {stderr[:300]}"
        )

    if not out_path.is_file():
        raise RuntimeError("codex exec did not create output file")

    try:
        data = _read_json(out_path)
    finally:
        try:
            out_path.unlink(missing_ok=True)  # type: ignore[call-arg]
        except Exception:
            pass

    return data


def _summarize_diff(before: MailProcedure, after: MailProcedure) -> str:
    lines: List[str] = []

    before_targets = list(before.target_folders or [])
    after_targets = list(after.target_folders or [])
    added_targets = [t for t in after_targets if t not in before_targets]
    removed_targets = [t for t in before_targets if t not in after_targets]
    if added_targets:
        lines.append(f"targets added: {', '.join(added_targets)}")
    if removed_targets:
        lines.append(f"targets removed: {', '.join(removed_targets)}")

    before_rules = {r.name: r for r in before.rules}
    after_rules = {r.name: r for r in after.rules}

    added_rules = [name for name in after_rules if name not in before_rules]
    removed_rules = [name for name in before_rules if name not in after_rules]

    if added_rules:
        lines.append(f"rules added: {', '.join(added_rules)}")
    if removed_rules:
        lines.append(f"rules removed: {', '.join(removed_rules)}")

    changed: List[str] = []
    fields = [
        "to_folder",
        "from_contains",
        "subject_contains",
        "max_messages",
        "newer_than_days",
        "unread_only",
    ]

    for name in before_rules.keys() & after_rules.keys():
        b = before_rules[name]
        a = after_rules[name]
        for field in fields:
            if getattr(b, field) != getattr(a, field):
                changed.append(
                    f"rule {name}: {field} {getattr(b, field)} -> {getattr(a, field)}"
                )

    lines.extend(changed)

    if not lines:
        return "no procedure changes"
    return "; ".join(lines)


def _newest_run_dir() -> Optional[Path]:
    if not RUNS_DIR.is_dir():
        return None
    candidates: List[Path] = []
    for child in RUNS_DIR.iterdir():
        if child.is_dir():
            if (child / "mail_report.md").is_file():
                candidates.append(child)
    if not candidates:
        for child in RUNS_DIR.iterdir():
            if child.is_dir():
                candidates.append(child)
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def _append_chat_log(
    *,
    run_dir: Path,
    objective: str,
    qa_pairs: List[Tuple[str, str]],
    diff_summary: str,
    report_path: Path,
    stage: str,
) -> None:
    log_path = run_dir / "chat_log.md"
    lines: List[str] = []
    lines.append(f"## Chat Log {datetime.now(timezone.utc).isoformat()} ({stage})")
    lines.append(f"Objective: {objective}")
    lines.append("")
    lines.append("Questions and Answers:")
    if qa_pairs:
        for q, a in qa_pairs:
            lines.append(f"- Q: {q}")
            lines.append(f"  A: {a}")
    else:
        lines.append("- None")
    lines.append("")
    lines.append(f"Procedure diff: {diff_summary}")
    lines.append("")
    lines.append(f"Final report: {report_path}")
    lines.append("")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
        if not lines[-1].endswith("\n"):
            handle.write("\n")




def _objective_implies_moves(objective: str) -> bool:
    low = objective.lower()
    if "move" in low:
        return True
    for token in ("1", "one", "single", "at least one"):
        if token in low:
            return True
    return False


def _objective_implies_execution(objective: str) -> bool:
    low = objective.lower()
    for token in (
        "execute",
        "continue",
        "use saved plan",
        "existing rule",
        "consolidation execution",
    ):
        if token in low:
            return True
    return False


def _load_json_file(path: Path) -> Optional[Dict[str, Any]]:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None


def _planned_moves_count(plan: Dict[str, Any]) -> int:
    total = 0
    for rule in plan.get("rules") or []:
        moves = rule.get("planned_moves")
        if isinstance(moves, list):
            total += len(moves)
        else:
            planned = rule.get("planned_uids") or []
            total += len(planned) if isinstance(planned, list) else 0
    return total


def _rules_with_zero_moves(plan: Dict[str, Any]) -> List[str]:
    names: List[str] = []
    for rule in plan.get("rules") or []:
        name = rule.get("name")
        moves = rule.get("planned_moves")
        planned = rule.get("planned_uids")
        count = 0
        if isinstance(moves, list):
            count = len(moves)
        elif isinstance(planned, list):
            count = len(planned)
        if name and count == 0:
            names.append(name)
    return names




def _scan_folder_summary(report_path: Path) -> str:
    if not report_path.is_file():
        return ""
    lines = report_path.read_text(encoding="utf-8", errors="replace").splitlines()
    in_folders = False
    folders = []
    for line in lines:
        if line.strip() == "## Folders (39)" or line.strip().startswith("## Folders"):
            in_folders = True
            continue
        if in_folders:
            if not line.strip():
                break
            if line.startswith("- "):
                folders.append(line[2:].strip())
    return ", ".join(folders)
def _run_executor(args: List[str]) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, "-m", "agent.autonomous.tools.mail_yahoo_imap_executor", *args]
    return subprocess.run(cmd, text=True, capture_output=True, encoding="utf-8", errors="ignore")


def _print_process_output(proc: subprocess.CompletedProcess[str]) -> None:
    if proc.stdout:
        print(proc.stdout.strip())
    if proc.stderr:
        print(proc.stderr.strip())


def run_mail_guided(objective: str | None = None) -> None:
    print("[MAIL GUIDED] Interactive mail session")
    if objective is None:
        objective = input("Objective: ").strip()
    if not objective:
        print("No objective provided. Exiting.")
        return

    proc_before = load_procedure()
    proc_json = json.dumps(proc_before.model_dump(), indent=2)
    execution_intent = _objective_implies_execution(objective)

    print("[MAIL GUIDED] Running IMAP scan...")
    scan_proc = _run_executor(["--scan-all-folders"])
    _print_process_output(scan_proc)
    latest_scan = _newest_run_dir()
    scan_report_path = latest_scan / "mail_report.md" if latest_scan else Path("unknown")
    scan_summary = _scan_folder_summary(scan_report_path)

    qa_pairs: List[Tuple[str, str]] = []
    proc_after = proc_before
    diff_summary = "no procedure changes"

    if execution_intent and not proc_before.rules:
        choice = input(
            "No existing rules found. Create a new rule for this execution? (y/N): "
        ).strip().lower()
        if choice != "y":
            print("[MAIL GUIDED] No rules to execute. Exiting.")
            return
        execution_intent = False

    if not execution_intent:
        questioner_prompt = (
            "You are the Questioner. Ask up to 5 clarifying questions to safely update "
            "the mail procedure. If no clarification is needed, return an empty list.\n"
            f"Objective: {objective}\n"
            f"Current procedure JSON:\n{proc_json}\n"
            f"IMAP scan folders: {scan_summary[:1000] if scan_summary else '(none)'}\n"
            "Return JSON: {questions: [..], rationale: string}."
        )

        print("[MAIL GUIDED] Running Questioner...")
        try:
            q_out = _run_codex_json(questioner_prompt, QUESTIONER_SCHEMA, profile="reason", timeout_seconds=60)
            questions = [q for q in (q_out.get("questions") or []) if isinstance(q, str)]
        except Exception as exc:
            print(f"[WARN] Questioner failed: {exc}")
            questions = []

        if questions:
            print("[MAIL GUIDED] Please answer the questions:")
            for q in questions:
                ans = input(f"- {q} ").strip()
                qa_pairs.append((q, ans))
        else:
            print("[MAIL GUIDED] No clarifying questions.")

        planner_prompt = (
            "You are the Planner. Update the mail procedure JSON based on the objective "
            "and Q/A. Keep protected_folders unless explicitly changed. Return JSON with "
            "a full 'procedure' object suitable for MailProcedure.\n"
            f"Objective: {objective}\n"
            f"Q/A: {json.dumps(qa_pairs, indent=2)}\n"
            f"Current procedure JSON:\n{proc_json}\n"
            f"IMAP scan folders: {scan_summary[:1000] if scan_summary else '(none)'}\n"
            "Return JSON: {procedure: {...}, summary: string}."
        )

        print("[MAIL GUIDED] Running Planner...")
        p_out = _run_codex_json(planner_prompt, PLANNER_SCHEMA, profile="reason", timeout_seconds=60)
        updated_proc_raw = p_out.get("procedure") or {}

        try:
            proc_after = MailProcedure.model_validate(updated_proc_raw)
        except Exception as exc:
            print(f"[WARN] Planner returned invalid procedure. Using existing procedure. Error: {exc}")
            proc_after = proc_before

        save_procedure(proc_after)
        diff_summary = _summarize_diff(proc_before, proc_after)
        print(f"[MAIL GUIDED] Procedure saved. Diff: {diff_summary}")
    else:
        print("[MAIL GUIDED] Execution intent detected; reusing existing rules without planner.")

    print("[MAIL GUIDED] Running IMAP dry-run...")
    dry_proc = _run_executor(["--dry-run"])
    _print_process_output(dry_proc)

    latest_run = _newest_run_dir()
    if latest_run is None:
        print("[WARN] Could not find runs directory for dry-run log.")
    else:
        report_path = latest_run / "mail_report.md"
        _append_chat_log(
            run_dir=latest_run,
            objective=objective,
            qa_pairs=qa_pairs,
            diff_summary=diff_summary,
            report_path=report_path,
            stage="dry-run",
        )

    # Auto-recover if objective implies moves but planned_moves == 0
    plan_data = _load_json_file(latest_run / "mail_plan.json") if latest_run else None
    if plan_data and _objective_implies_moves(objective):
        zero_rules = _rules_with_zero_moves(plan_data)
        if zero_rules:
            print("[MAIL GUIDED] No planned moves; running scan-all-folders...")
            scan_proc = _run_executor(["--scan-all-folders"])
            _print_process_output(scan_proc)

            latest_run = _newest_run_dir()
            scan_data = _load_json_file(latest_run / "mail_scan.json") if latest_run else None
            if scan_data:
                rules_scan = scan_data.get("rules") or {}
                if isinstance(rules_scan, dict):
                    proc_update = load_procedure()
                    updated = False
                    for rule_name in zero_rules:
                        folders_map = rules_scan.get(rule_name) or {}
                        if not isinstance(folders_map, dict) or not folders_map:
                            continue
                        folders_list = [
                            f"{folder}({count})"
                            for folder, count in folders_map.items()
                            if isinstance(count, int) and count > 0
                        ]
                        if not folders_list:
                            continue
                        prompt = (
                            f"I found matches in these folders: {', '.join(folders_list)}. "
                            f"Choose folders to search for rule {rule_name} (comma-separated), "
                            "or press Enter to keep current: "
                        )
                        choice = input(prompt).strip()
                        if choice:
                            new_folders = [c.strip() for c in choice.split(",") if c.strip()]
                            for rule in proc_update.rules:
                                if rule.name == rule_name:
                                    rule.search_folders = new_folders
                                    updated = True
                    if updated:
                        save_procedure(proc_update)

            print("[MAIL GUIDED] Re-running IMAP dry-run after scan...")
            dry_proc = _run_executor(["--dry-run"])
            _print_process_output(dry_proc)

            latest_run = _newest_run_dir()
            if latest_run is not None:
                report_path = latest_run / "mail_report.md"
                _append_chat_log(
                    run_dir=latest_run,
                    objective=objective,
                    qa_pairs=qa_pairs,
                    diff_summary=diff_summary,
                    report_path=report_path,
                    stage="dry-run-retry",
                )

            plan_data = _load_json_file(latest_run / "mail_plan.json") if latest_run else None

    if plan_data and _objective_implies_moves(objective):
        if _planned_moves_count(plan_data) == 0:
            print("[MAIL GUIDED] Planned moves still 0; stopping before execute.")
            return

    if plan_data and _planned_moves_count(plan_data) == 0:
        print("No moves planned; ending session.")
        return

    confirm = input("Type EXECUTE to run the move (exactly): ").strip()
    if confirm != "EXECUTE":
        print("[MAIL GUIDED] EXECUTE not confirmed. Exiting.")
        return

    print("[MAIL GUIDED] Running IMAP execute...")
    exec_proc = _run_executor(["--execute", "--max-per-rule", "1"])
    _print_process_output(exec_proc)

    latest_run = _newest_run_dir()
    report_path = latest_run / "mail_report.md" if latest_run else Path("unknown")

    critic_prompt = (
        "You are the Critic. Summarize the run and suggest safe procedure tweaks. "
        "Return JSON: {summary: string, suggestions: [..]}.\n"
        f"Objective: {objective}\n"
        f"Q/A: {json.dumps(qa_pairs, indent=2)}\n"
        f"Procedure diff: {diff_summary}\n"
        f"Dry-run output:\n{(dry_proc.stdout or '')[:2000]}\n"
        f"Execute output:\n{(exec_proc.stdout or '')[:2000]}\n"
        f"Final report path: {report_path}"
    )

    print("[MAIL GUIDED] Running Critic...")
    c_out = _run_codex_json(critic_prompt, CRITIC_SCHEMA, profile="reason", timeout_seconds=60)
    critic_summary = c_out.get("summary", "")
    critic_suggestions = c_out.get("suggestions") or []

    if critic_summary:
        print(f"[MAIL GUIDED] Critic summary: {critic_summary}")
    if critic_suggestions:
        print("[MAIL GUIDED] Critic suggestions:")
        for suggestion in critic_suggestions:
            print(f"- {suggestion}")

    if latest_run is not None:
        _append_chat_log(
            run_dir=latest_run,
            objective=objective,
            qa_pairs=qa_pairs,
            diff_summary=diff_summary,
            report_path=report_path,
            stage="execute",
        )

    if exec_proc.returncode != 0:
        raise SystemExit(exec_proc.returncode)


def main() -> None:
    parser = argparse.ArgumentParser(description="Guided mail workflow")
    parser.add_argument("--objective", help="Objective text for the mail session")
    args = parser.parse_args()
    run_mail_guided(args.objective)


if __name__ == "__main__":
    main()
