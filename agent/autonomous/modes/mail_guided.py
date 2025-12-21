from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from agent.memory.procedures.mail_yahoo import load_procedure, save_procedure, MailProcedure

REPO_ROOT = Path(__file__).resolve().parents[3]
RUNS_DIR = REPO_ROOT / "runs"
PROGRESS_INTERVAL_DEFAULT = 2.0
HEARTBEAT_AFTER_SECONDS = 10.0

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

FOLDER_MERGE_RULE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "name": {"type": "string"},
        "to_folder": {"type": "string"},
        "source_folders": {"type": "array", "items": {"type": "string"}},
        "max_messages": {"type": "integer"},
    },
    "required": ["name", "to_folder", "source_folders", "max_messages"],
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
        "folder_merge_rules": {"type": "array", "items": FOLDER_MERGE_RULE_SCHEMA},
        "folder_merge_mapping": {
            "type": "object",
            "additionalProperties": {"type": "string"},
        },
        "protected_folders": {"type": "array", "items": {"type": "string"}},
        "last_updated_utc": {"type": "string"},
    },
    "required": [
        "version",
        "provider",
        "account_label",
        "target_folders",
        "rules",
        "folder_merge_rules",
        "folder_merge_mapping",
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

ANSWER_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "answers": {
            "type": "object",
            "additionalProperties": {"type": "string"},
        },
        "missing_required": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["answers", "missing_required"],
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

FOLDER_GROUPER_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "targets": {"type": "array", "items": {"type": "string"}},
        "mapping": {
            "type": "object",
            "additionalProperties": {"type": "string"},
        },
    },
    "required": ["targets", "mapping"],
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

    before_merge = {r.name: r for r in before.folder_merge_rules}
    after_merge = {r.name: r for r in after.folder_merge_rules}
    added_merge = [name for name in after_merge if name not in before_merge]
    removed_merge = [name for name in before_merge if name not in after_merge]
    if added_merge:
        lines.append(f"merge rules added: {', '.join(added_merge)}")
    if removed_merge:
        lines.append(f"merge rules removed: {', '.join(removed_merge)}")

    merge_fields = ["to_folder", "source_folders", "max_messages"]
    for name in before_merge.keys() & after_merge.keys():
        b = before_merge[name]
        a = after_merge[name]
        for field in merge_fields:
            if getattr(b, field) != getattr(a, field):
                lines.append(
                    f"merge rule {name}: {field} {getattr(b, field)} -> {getattr(a, field)}"
                )

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


def _objective_implies_folder_merge(objective: str) -> bool:
    low = objective.lower()
    phrases = (
        "consolidate folders",
        "consolidate my folders",
        "reduce folders",
        "merge folders",
        "folder consolidation",
        "folder merge",
    )
    return any(phrase in low for phrase in phrases)


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


def _write_state(run_dir: Path, state: str) -> None:
    path = run_dir / "session_state.json"
    payload = {"state": state, "time_utc": datetime.now(timezone.utc).isoformat()}
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _read_state(run_dir: Path) -> Optional[str]:
    data = _load_json_file(run_dir / "session_state.json")
    if not data:
        return None
    return data.get("state")


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


def _objective_disables_folder_creation(objective: str) -> bool:
    low = objective.lower()
    return any(
        phrase in low
        for phrase in (
            "do not create folders",
            "do not create any new folders",
            "do not create new folders",
            "no new folders",
        )
    )


def _print_artifact_paths(run_dir: Optional[Path]) -> None:
    if not run_dir:
        return
    report_path = run_dir / "mail_report.md"
    chat_log_path = run_dir / "chat_log.md"
    print(f"[MAIL GUIDED] Report path: {report_path}")
    print(f"[MAIL GUIDED] Chat log path: {chat_log_path}")


def _questions_path(run_dir: Path) -> Path:
    return run_dir / "questions.json"


def _answers_path(run_dir: Path) -> Path:
    return run_dir / "answers.json"


def _write_questions(run_dir: Path, questions: List[str]) -> None:
    payload = {
        "questions": [
            {"id": f"q{idx+1}", "text": text, "required": True}
            for idx, text in enumerate(questions)
        ]
    }
    _questions_path(run_dir).write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )


def _load_questions(run_dir: Path) -> Optional[Dict[str, Any]]:
    return _load_json_file(_questions_path(run_dir))


def _load_answers(run_dir: Path) -> Optional[Dict[str, Any]]:
    return _load_json_file(_answers_path(run_dir))
def _run_executor(
    args: List[str],
    *,
    phase: Optional[str] = None,
    heartbeat_after: float = HEARTBEAT_AFTER_SECONDS,
) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, "-m", "agent.autonomous.tools.mail_yahoo_imap_executor", *args]
    proc = subprocess.Popen(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="ignore",
    )
    start = time.monotonic()
    last_heartbeat = start
    while proc.poll() is None:
        time.sleep(1.0)
        if phase and (time.monotonic() - last_heartbeat) >= heartbeat_after:
            elapsed = time.monotonic() - start
            print(f"[MAIL GUIDED] Still working... elapsed={elapsed:.1f}s")
            last_heartbeat = time.monotonic()
    stdout, stderr = proc.communicate()
    return subprocess.CompletedProcess(cmd, proc.returncode, stdout, stderr)


def _print_process_output(proc: subprocess.CompletedProcess[str]) -> None:
    if proc.stdout:
        print(proc.stdout.strip())
    if proc.stderr:
        print(proc.stderr.strip())


def _progress_args() -> List[str]:
    return ["--progress", "--progress-interval", str(PROGRESS_INTERVAL_DEFAULT)]


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
    no_create_folders = _objective_disables_folder_creation(objective)
    if no_create_folders:
        print("[MAIL GUIDED] Folder creation disabled by objective.")

    print("[MAIL GUIDED] Phase: SCAN_ALL_FOLDERS (this may take a few minutes)")
    scan_args = ["--scan-all-folders", *_progress_args()]
    if no_create_folders:
        scan_args.append("--no-create-folders")
    scan_proc = _run_executor(scan_args, phase="SCAN_ALL_FOLDERS")
    _print_process_output(scan_proc)
    latest_scan = _newest_run_dir()
    scan_report_path = latest_scan / "mail_report.md" if latest_scan else Path("unknown")
    scan_summary = _scan_folder_summary(scan_report_path)
    if latest_scan is not None:
        _write_state(latest_scan, "SCAN_DONE")

    qa_pairs: List[Tuple[str, str]] = []
    folder_merge_intent = _objective_implies_folder_merge(objective)

    if latest_scan is not None:
        existing_questions = _load_questions(latest_scan)
        existing_answers = _load_answers(latest_scan)
        if existing_questions and not existing_answers:
            print("[MAIL GUIDED] Found pending questions. Please answer below.")
            _write_state(latest_scan, "WAITING_FOR_ANSWERS")
            questions_list = existing_questions.get("questions") or []
            qa_pairs: List[Tuple[str, str]] = []
            for q in questions_list:
                qid = q.get("id") or "q"
                qtext = q.get("text") or ""
                ans = input(f"- {qid}: {qtext} ").strip()
                qa_pairs.append((qid, ans))

            print("Answer the questions, then type CONTINUE.")
            confirm = input("> ").strip().lower()
            if confirm != "continue":
                print("[MAIL GUIDED] CONTINUE not confirmed. Exiting.")
                return

            raw_answers = {"answers": {qid: ans for qid, ans in qa_pairs}}
            _answers_path(latest_scan).write_text(
                json.dumps(raw_answers, indent=2), encoding="utf-8"
            )

            parser_prompt = (
                "You are AnswerParser. Validate answers for required questions. "
                "Return JSON: {answers: {qid: answer}, missing_required: [qid...]}. "
                f"Questions: {json.dumps(questions_list)}\n"
                f"Answers: {json.dumps(raw_answers)}"
            )
            parsed = _run_codex_json(parser_prompt, ANSWER_SCHEMA, profile="reason", timeout_seconds=60)
            missing = parsed.get("missing_required") or []
            got = sorted([k for k, v in (parsed.get("answers") or {}).items() if v])
            if missing:
                print(
                    f"[MAIL GUIDED] I captured answers for {', '.join(got)}. "
                    f"Missing: {', '.join(missing)}. Please answer: {', '.join(missing)}"
                )
                _write_state(latest_scan, "WAITING_FOR_ANSWERS")
                return
            print(f"[MAIL GUIDED] I captured answers for: {', '.join(got)}")
            _answers_path(latest_scan).write_text(
                json.dumps(parsed, indent=2), encoding="utf-8"
            )
            _write_state(latest_scan, "ANSWERS_CONFIRMED")
            return

    if latest_scan is not None:
        parsed_answers = _load_answers(latest_scan)
        if parsed_answers and parsed_answers.get("answers"):
            qa_pairs = list(parsed_answers["answers"].items())
            _write_state(latest_scan, "ANSWERS_CONFIRMED")

    if folder_merge_intent:
        if latest_scan is None:
            print("[WARN] No run directory found; cannot load folder list.")
            return
        if not qa_pairs:
            questions = [
                "Which top-level target folders should everything be consolidated into? (comma-separated)",
                "Any folders to exclude or keep as-is? (comma-separated or 'none')",
            ]
            _write_questions(latest_scan, questions)
            _write_state(latest_scan, "WAITING_FOR_ANSWERS")
            print("[MAIL GUIDED] Questions saved. Answer the questions, then type CONTINUE.")
            print(f"[MAIL GUIDED] Questions path: {_questions_path(latest_scan)}")
            return

        folder_list = scan_summary[:2000] if scan_summary else "(none)"
        grouper_prompt = (
            "You are FolderGrouper. Consolidate existing folders by moving ALL messages "
            "from source folders into target folders. Propose 5-6 target folders, "
            "and map every existing folder to exactly one target. "
            "Do NOT use sender-based or subject-based searches. "
            "Never output FROM/SUBJECT queries for folder consolidation.\n"
            f"Objective: {objective}\n"
            f"Q/A: {json.dumps(qa_pairs, indent=2)}\n"
            f"IMAP folder list: {folder_list}\n"
            "Return JSON: {targets: [..], mapping: {OldFolder: Target, ...}}."
        )
        print("[MAIL GUIDED] Running FolderGrouper...")
        grouper_out = _run_codex_json(
            grouper_prompt, FOLDER_GROUPER_SCHEMA, profile="reason", timeout_seconds=60
        )
        targets = [t for t in (grouper_out.get("targets") or []) if isinstance(t, str)]
        mapping = {
            k: v
            for k, v in (grouper_out.get("mapping") or {}).items()
            if isinstance(k, str) and isinstance(v, str)
        }
        rules = []
        for target in targets:
            sources = [
                folder
                for folder, mapped in mapping.items()
                if mapped == target and folder != target
            ]
            if sources:
                rules.append(
                    {
                        "name": f"merge_{target}",
                        "to_folder": target,
                        "source_folders": sources,
                        "max_messages": 500,
                    }
                )

        proc_after = MailProcedure.model_validate(
            {
                **proc_before.model_dump(),
                "target_folders": targets,
                "folder_merge_rules": rules,
                "folder_merge_mapping": mapping,
            }
        )
        save_procedure(proc_after)
        diff_summary = _summarize_diff(proc_before, proc_after)
        print(f"[MAIL GUIDED] Procedure saved. Diff: {diff_summary}")
        if latest_scan is not None:
            _write_state(latest_scan, "PLANNING")

        print("[MAIL GUIDED] Phase: FOLDER_MERGE_PLANNING")
        dry_args = ["--dry-run", "--mode", "folder_merge", *_progress_args()]
        if no_create_folders:
            dry_args.append("--no-create-folders")
        dry_proc = _run_executor(dry_args, phase="FOLDER_MERGE_PLANNING")
        _print_process_output(dry_proc)
        latest_run = _newest_run_dir()
        if latest_run is not None:
            _write_state(latest_run, "DRY_RUN")

        latest_run = _newest_run_dir()
        if latest_run is None:
            print("[WARN] Could not find runs directory for dry-run log.")
            return

        report_path = latest_run / "mail_report.md"
        _append_chat_log(
            run_dir=latest_run,
            objective=objective,
            qa_pairs=qa_pairs,
            diff_summary=diff_summary,
            report_path=report_path,
            stage="dry-run",
        )
        _print_artifact_paths(latest_run)

        plan_data = _load_json_file(latest_run / "mail_plan.json")
        if plan_data and _planned_moves_count(plan_data) == 0:
            print("No moves planned; ending session.")
            _print_artifact_paths(latest_run)
            return

        confirm = input("Type EXECUTE to run the move (exactly): ").strip()
        if confirm.lower() != "execute":
            print("[MAIL GUIDED] EXECUTE not confirmed. Exiting.")
            _print_artifact_paths(latest_run)
            return

        print("[MAIL GUIDED] Phase: FOLDER_MERGE_EXECUTE")
        exec_args = ["--execute", "--mode", "folder_merge", *_progress_args()]
        if no_create_folders:
            exec_args.append("--no-create-folders")
        exec_args.extend(["--plan-path", str(latest_run / "mail_plan.json")])
        exec_proc = _run_executor(exec_args, phase="FOLDER_MERGE_EXECUTE")
        _print_process_output(exec_proc)
        if latest_run is not None:
            _write_state(latest_run, "EXECUTING")

        latest_run = _newest_run_dir()
        report_path = latest_run / "mail_report.md" if latest_run else Path("unknown")
        if latest_run is not None:
            _append_chat_log(
                run_dir=latest_run,
                objective=objective,
                qa_pairs=qa_pairs,
                diff_summary=diff_summary,
                report_path=report_path,
                stage="execute",
            )
            _print_artifact_paths(latest_run)
            _write_state(latest_run, "DONE")

        if exec_proc.returncode != 0:
            raise SystemExit(exec_proc.returncode)
        return

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
        questions: List[str] = []
        if not qa_pairs:
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
            if latest_scan is None:
                print("[WARN] No run directory found; cannot persist questions.")
                return
            _write_questions(latest_scan, questions)
            _write_state(latest_scan, "WAITING_FOR_ANSWERS")
            print("[MAIL GUIDED] Questions saved. Answer the questions, then type CONTINUE.")
            print(f"[MAIL GUIDED] Questions path: {_questions_path(latest_scan)}")
            return
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
        if qa_pairs:
            answered = ", ".join([q for q, _ in qa_pairs])
            print(f"[MAIL GUIDED] Planner used your answers: {answered}")
        if latest_scan is not None:
            _write_state(latest_scan, "PLANNING")
    else:
        print("[MAIL GUIDED] Execution intent detected; reusing existing rules without planner.")

    print("[MAIL GUIDED] Phase: RULES_DRY_RUN")
    dry_args = ["--dry-run", *_progress_args()]
    if no_create_folders:
        dry_args.append("--no-create-folders")
    dry_proc = _run_executor(dry_args, phase="RULES_DRY_RUN")
    _print_process_output(dry_proc)
    latest_run = _newest_run_dir()
    if latest_run is not None:
        _write_state(latest_run, "DRY_RUN")

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
        _print_artifact_paths(latest_run)

    # Auto-recover if objective implies moves but planned_moves == 0
    plan_data = _load_json_file(latest_run / "mail_plan.json") if latest_run else None
    if plan_data and _objective_implies_moves(objective):
        zero_rules = _rules_with_zero_moves(plan_data)
        if zero_rules:
            print("[MAIL GUIDED] Phase: SCAN_ALL_FOLDERS (this may take a few minutes)")
            scan_args = ["--scan-all-folders", *_progress_args()]
            if no_create_folders:
                scan_args.append("--no-create-folders")
            scan_proc = _run_executor(scan_args, phase="SCAN_ALL_FOLDERS")
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

            print("[MAIL GUIDED] Phase: RULES_DRY_RUN (after scan)")
            dry_args = ["--dry-run", *_progress_args()]
            if no_create_folders:
                dry_args.append("--no-create-folders")
            dry_proc = _run_executor(dry_args, phase="RULES_DRY_RUN")
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
                _print_artifact_paths(latest_run)

            plan_data = _load_json_file(latest_run / "mail_plan.json") if latest_run else None

    if plan_data and _objective_implies_moves(objective):
        if _planned_moves_count(plan_data) == 0:
            print("[MAIL GUIDED] Planned moves still 0; stopping before execute.")
            _print_artifact_paths(latest_run)
            return

    if plan_data and _planned_moves_count(plan_data) == 0:
        print("No moves planned; ending session.")
        _print_artifact_paths(latest_run)
        return

    confirm = input("Type EXECUTE to run the move (exactly): ").strip()
    if confirm.lower() != "execute":
        print("[MAIL GUIDED] EXECUTE not confirmed. Exiting.")
        _print_artifact_paths(latest_run)
        return

    print("[MAIL GUIDED] Phase: RULES_EXECUTE")
    exec_args = ["--execute", *_progress_args()]
    if no_create_folders:
        exec_args.append("--no-create-folders")
    if latest_run is not None:
        exec_args.extend(["--plan-path", str(latest_run / "mail_plan.json")])
    exec_proc = _run_executor(exec_args, phase="RULES_EXECUTE")
    _print_process_output(exec_proc)
    if latest_run is not None:
        _write_state(latest_run, "EXECUTING")

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
    critic_summary = ""
    critic_suggestions = []
    try:
        c_out = _run_codex_json(critic_prompt, CRITIC_SCHEMA, profile="reason", timeout_seconds=60)
        critic_summary = c_out.get("summary", "")
        critic_suggestions = c_out.get("suggestions") or []
    except Exception as exc:
        print(f"[WARN] Critic failed: {exc}")

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
        _print_artifact_paths(latest_run)
        _write_state(latest_run, "DONE")

    if exec_proc.returncode != 0:
        raise SystemExit(exec_proc.returncode)


def main() -> None:
    parser = argparse.ArgumentParser(description="Guided mail workflow")
    parser.add_argument("--objective", help="Objective text for the mail session")
    args = parser.parse_args()
    run_mail_guided(args.objective)


if __name__ == "__main__":
    main()
