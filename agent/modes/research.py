from __future__ import annotations

"""Research mode - iterative deep research with refinement."""

import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime
from contextlib import nullcontext
from pathlib import Path

try:
    from colorama import Fore, Style

    GREEN, RED, CYAN, YELLOW, RESET = (
        Fore.GREEN,
        Fore.RED,
        Fore.CYAN,
        Fore.YELLOW,
        Style.RESET_ALL,
    )
except Exception:
    GREEN = RED = CYAN = YELLOW = RESET = ""

BASE_DIR = Path(__file__).resolve().parents[1]  # .../agent
REPO_ROOT = BASE_DIR.parent


def _codex_command() -> list[str]:
    cmd = shutil.which("codex") or shutil.which("codex.ps1")
    if cmd and cmd.lower().endswith(".ps1"):
        return ["powershell", "-File", cmd]
    return [cmd or "codex"]


def _bool_env(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "y", "on"}


def _int_env(name: str, default: int) -> int:
    val = os.getenv(name)
    if val is None or not str(val).strip():
        return default
    try:
        return int(str(val).strip())
    except Exception:
        return default


def _extract_bullets(text: str, *, limit: int = 5) -> list[str]:
    items: list[str] = []
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line[0] in {"-", "*"}:
            line = line[1:].strip()
        elif len(line) > 2 and line[:2].isdigit() and line[1] == ".":
            line = line[2:].strip()
        if line:
            items.append(line)
        if len(items) >= limit:
            break
    return items


_URL_RE = re.compile(r"https?://[^\s)>\"]+")


def _short_label(text: str, *, max_words: int = 6, max_chars: int = 40) -> str:
    words = re.findall(r"\S+", text or "")
    if not words:
        return ""
    label = " ".join(words[:max_words])
    if len(label) > max_chars:
        label = label[: max_chars - 3].rstrip() + "..."
    return label


def _strip_sources_section(markdown: str) -> str:
    if not markdown:
        return markdown
    lower = markdown.lower()
    idx = lower.find("\n## sources")
    if idx == -1:
        idx = lower.find("## sources")
    if idx == -1:
        return markdown
    return markdown[:idx].rstrip()


def _extract_sources(markdown: str) -> list[str]:
    seen: set[str] = set()
    urls: list[str] = []
    for raw in _URL_RE.findall(markdown or ""):
        cleaned = raw.rstrip(".,;:])}>\"'")
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            urls.append(cleaned)
    return urls


def _append_sources_section(markdown: str) -> str:
    if not markdown:
        return markdown
    base = _strip_sources_section(markdown)
    urls = _extract_sources(markdown)
    if not urls:
        return base
    section = "\n\n## Sources\n" + "\n".join(f"- {u}" for u in urls)
    return base.rstrip() + section


def _log_event(log: list[str], kind: str, message: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    log.append(f"{ts} [{kind}] {message}")


def _select_research_profile() -> dict:
    profiles = {
        "1": {
            "name": "light",
            "max_gap_passes": 1,
            "min_subtopics": 3,
            "checklist": False,
            "review_passes": 0,
            "max_review_questions": 0,
            "min_sources_per_subtopic": 2,
        },
        "2": {
            "name": "balanced",
            "max_gap_passes": 2,
            "min_subtopics": 4,
            "checklist": False,
            "review_passes": 1,
            "max_review_questions": 3,
            "min_sources_per_subtopic": 3,
        },
        "3": {
            "name": "deep",
            "max_gap_passes": 5,
            "min_subtopics": 6,
            "checklist": False,
            "review_passes": 3,
            "max_review_questions": 5,
            "min_sources_per_subtopic": 5,
        },
        "4": {
            "name": "checklist",
            "max_gap_passes": 2,
            "min_subtopics": 5,
            "checklist": True,
            "review_passes": 1,
            "max_review_questions": 3,
            "min_sources_per_subtopic": 4,
        },
    }
    aliases = {
        "light": "1",
        "l": "1",
        "balanced": "2",
        "b": "2",
        "deep": "3",
        "d": "3",
        "checklist": "4",
        "c": "4",
    }

    env_choice = (os.getenv("TREYS_AGENT_RESEARCH_MODE") or "").strip().lower()
    if env_choice:
        choice_key = aliases.get(env_choice, env_choice)
        profile = profiles.get(choice_key)
        if profile:
            print(f"{YELLOW}[DEPTH]{RESET} {profile['name']} (from TREYS_AGENT_RESEARCH_MODE)")
            return profile

    print(
        f"{YELLOW}[DEPTH]{RESET} Choose research depth:\n"
        "  1) Light     (1 self-check pass)\n"
        "  2) Balanced  (1-2 self-check passes)\n"
        "  3) Deep      (up to 5 self-check passes)\n"
        "  4) Checklist (>=5 subtopics + coverage checklist)\n"
    )
    choice = input(f"{GREEN}Select 1-4 (default 2):{RESET} ").strip().lower()
    if not choice:
        choice = "2"
    choice_key = aliases.get(choice, choice)
    profile = profiles.get(choice_key, profiles["2"])
    print(f"{YELLOW}[DEPTH]{RESET} Using: {profile['name']}")
    return profile


def _gap_questions(topic: str, subtopic: str, answers: str, notes: str) -> list[str]:
    prompt = f"""Topic: {topic}
Subtopic: {subtopic}
User clarifications: {answers}

Current notes:
{notes[:4000]}

List up to 3 missing angles or questions that would deepen this subtopic.
Output bullets only (no prose)."""
    gap_text = _call_codex(prompt, allow_tools=False, label="GAPS", context=subtopic)
    if gap_text.startswith("[CODEX ERROR]"):
        return []
    return _extract_bullets(gap_text, limit=3)


def _coverage_check(topic: str, answers: str, notes: str, checklist: list[str]) -> list[str]:
    checklist_block = "\n".join(f"- {c}" for c in checklist)
    prompt = f"""Topic: {topic}
User clarifications: {answers}

Checklist:
{checklist_block}

Notes:
{notes[:6000]}

List any checklist items that are missing or weak.
Output bullets only. If complete, output "none"."""
    resp = _call_codex(prompt, allow_tools=False, label="CHECK", context=topic)
    if resp.startswith("[CODEX ERROR]"):
        return []
    items = _extract_bullets(resp, limit=8)
    if any(i.lower().strip() == "none" for i in items):
        return []
    return items


def _review_questions(topic: str, answers: str, report: str, *, limit: int) -> list[str]:
    prompt = f"""Topic: {topic}
User clarifications: {answers}

Current report:
{report[:6000]}

List up to {limit} follow-up questions that would deepen or verify the report.
Focus on weak evidence, contradictions, or missing angles.
Output bullets only."""
    resp = _call_codex(prompt, allow_tools=False, label="REVIEW", context=topic)
    if resp.startswith("[CODEX ERROR]"):
        return []
    return _extract_bullets(resp, limit=limit)


def _call_codex(
    prompt: str,
    *,
    allow_tools: bool,
    label: str = "CODEX",
    context: str | None = None,
    timeout_seconds: int | None = None,
    show_progress: bool | None = None,
) -> str:
    show_progress = _bool_env("TREYS_AGENT_PROGRESS", True) if show_progress is None else show_progress
    use_json_events = _bool_env("TREYS_AGENT_JSON_EVENTS", True) if show_progress else False
    heartbeat_seconds = _int_env("TREYS_AGENT_HEARTBEAT_SECONDS", 20)
    context_label = _short_label(context or "")

    # Note: `--search` is a global flag (must appear before the `exec` subcommand).
    cmd: list[str] = _codex_command() + ["--dangerously-bypass-approvals-and-sandbox"]
    if allow_tools:
        cmd += ["--search"]
    cmd += ["exec"]
    if use_json_events:
        cmd += ["--json"]
    if not allow_tools:
        cmd += ["--disable", "shell_tool", "--disable", "rmcp_client"]

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"

    if not show_progress:
        try:
            try:
                from agent.ui.spinner import Spinner

                spinner_ctx = Spinner(label) if sys.stdout.isatty() else nullcontext()
            except Exception:
                spinner_ctx = nullcontext()

            with spinner_ctx:
                proc = subprocess.run(
                    cmd,
                    input=prompt,
                    text=True,
                    encoding="utf-8",
                    errors="ignore",
                    capture_output=True,
                    env=env,
                    cwd=str(REPO_ROOT),
                    timeout=timeout_seconds or int(os.getenv("CODEX_TIMEOUT_SECONDS", "600")),
                )
        except FileNotFoundError:
            return "[CODEX ERROR] Codex CLI not found on PATH."
        except subprocess.TimeoutExpired:
            timeout_s = timeout_seconds or int(os.getenv("CODEX_TIMEOUT_SECONDS", "600"))
            return (
                f"[CODEX ERROR] Codex CLI timed out after {timeout_s}s. "
                "Try setting CODEX_TIMEOUT_SECONDS=900 and retry."
            )

        if proc.returncode != 0:
            error = proc.stderr.strip() if proc.stderr else "Unknown error"
            return f"[CODEX ERROR] {error}"

        return proc.stdout.strip() if proc.stdout else ""

    # Progress / event mode (best-effort, avoids exposing chain-of-thought).
    start_time = time.time()
    timeout_s = timeout_seconds or int(os.getenv("CODEX_TIMEOUT_SECONDS", "600"))
    stdout_lines: list[str] = []
    stderr_lines: list[str] = []
    final_parts: list[str] = []
    stop_event = threading.Event()
    status_lock = threading.Lock()
    last_status: list[str] = [""]

    def _status(msg: str) -> None:
        with status_lock:
            if context_label:
                msg = f"{msg} ({context_label})"
            if msg and msg != last_status[0]:
                print(f"{YELLOW}[{label}]{RESET} {msg}")
                last_status[0] = msg

    def _heartbeat() -> None:
        if heartbeat_seconds <= 0:
            return
        while not stop_event.wait(heartbeat_seconds):
            elapsed = int(time.time() - start_time)
            if context_label:
                print(f"{YELLOW}[{label}]{RESET} still working... {elapsed}s ({context_label})")
            else:
                print(f"{YELLOW}[{label}]{RESET} still working... {elapsed}s")

    def _handle_json_event(obj: dict) -> None:
        event_type = str(obj.get("type") or "").lower()
        if event_type == "turn.started":
            _status("planning...")
            return
        if "tool" in event_type:
            _status("using tools...")
            return
        if event_type == "item.completed":
            item = obj.get("item") or {}
            item_type = str(item.get("type") or "").lower()
            if item_type == "reasoning":
                _status("thinking...")
                return
            if item_type in {"agent_message", "assistant_message", "message", "final"}:
                text = item.get("text")
                if isinstance(text, str) and text.strip():
                    final_parts.append(text.strip())
                _status("drafting response...")
                return
            if "tool" in item_type:
                _status("using tools...")
                return

    def _read_stream(stream, sink, *, parse_json: bool) -> None:
        try:
            for line in iter(stream.readline, ""):
                if not line:
                    break
                sink.append(line)
                if parse_json:
                    try:
                        obj = json.loads(line.strip())
                        if isinstance(obj, dict):
                            _handle_json_event(obj)
                    except Exception:
                        continue
        finally:
            try:
                stream.close()
            except Exception:
                pass

    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="ignore",
            env=env,
            cwd=str(REPO_ROOT),
            bufsize=1,
        )
    except FileNotFoundError:
        return "[CODEX ERROR] Codex CLI not found on PATH."

    hb = threading.Thread(target=_heartbeat, daemon=True)
    hb.start()

    threads: list[threading.Thread] = []
    if proc.stdout is not None:
        t_out = threading.Thread(
            target=_read_stream,
            args=(proc.stdout, stdout_lines),
            kwargs={"parse_json": use_json_events},
            daemon=True,
        )
        t_out.start()
        threads.append(t_out)
    if proc.stderr is not None:
        t_err = threading.Thread(
            target=_read_stream,
            args=(proc.stderr, stderr_lines),
            kwargs={"parse_json": False},
            daemon=True,
        )
        t_err.start()
        threads.append(t_err)

    try:
        if proc.stdin is not None:
            proc.stdin.write(prompt)
            proc.stdin.close()
        proc.wait(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        proc.kill()
        stop_event.set()
        elapsed = int(time.time() - start_time)
        return (
            f"[CODEX ERROR] Codex CLI timed out after {elapsed}s. "
            "Try setting CODEX_TIMEOUT_SECONDS=900 and retry."
        )
    finally:
        stop_event.set()

    for t in threads:
        t.join(timeout=1)
    hb.join(timeout=1)

    if proc.returncode != 0:
        err = "".join(stderr_lines).strip() or "Unknown error"
        return f"[CODEX ERROR] {err}"

    if use_json_events:
        if final_parts:
            return "\n".join(final_parts).strip()
        # Fallback to raw output if parsing failed.
        return "".join(stdout_lines).strip()

    return "".join(stdout_lines).strip()


def _research_staged(topic: str, answers: str, profile: dict, log: list[str]) -> str:
    min_subtopics = int(profile.get("min_subtopics") or 3)
    max_gap_passes = int(profile.get("max_gap_passes") or 1)
    checklist_mode = bool(profile.get("checklist"))
    review_passes = int(profile.get("review_passes") or 0)
    max_review_questions = int(profile.get("max_review_questions") or 0)
    min_sources = int(profile.get("min_sources_per_subtopic") or 2)
    checklist_items = [
        "Definitions/background",
        "Current state / recent updates",
        "Key players / stakeholders",
        "Quantitative data (market size, metrics, stats)",
        "Risks / limitations / counterpoints",
        "Practical implications / recommendations",
    ]

    print(f"{YELLOW}[PLAN]{RESET} Generating subtopics...")
    plan_prompt = f"""User wants to research: {topic}
User clarifications: {answers}

Return {min_subtopics}-5 focused subtopics as bullet points. Output only bullets."""
    if checklist_mode:
        plan_prompt += "\nEnsure coverage of: " + "; ".join(checklist_items)
    _log_event(log, "PLAN", f"Generating subtopics (min {min_subtopics})")
    plan_text = _call_codex(plan_prompt, allow_tools=False, label="PLAN", context=topic)
    if plan_text.startswith("[CODEX ERROR]"):
        _log_event(log, "ERROR", plan_text)
        return plan_text

    subtopics = _extract_bullets(plan_text, limit=8)
    if len(subtopics) < min_subtopics:
        expand_prompt = f"""We need at least {min_subtopics} unique subtopics.
Current list:
{chr(10).join(f"- {s}" for s in subtopics)}

Add more unique subtopics to reach {min_subtopics}. Output bullets only."""
        extra = _call_codex(expand_prompt, allow_tools=False, label="PLAN", context=topic)
        if not extra.startswith("[CODEX ERROR]"):
            subtopics.extend(_extract_bullets(extra, limit=8))
        seen = set()
        subtopics = [s for s in subtopics if not (s.lower() in seen or seen.add(s.lower()))]
    if not subtopics:
        subtopics = [topic]
    _log_event(log, "PLAN", f"Subtopics: {', '.join(subtopics[:10])}")

    parts: list[str] = []
    sub_timeout = _int_env("TREYS_AGENT_SUBTASK_TIMEOUT_SECONDS", 240)
    total = len(subtopics)
    for idx, sub in enumerate(subtopics, 1):
        print(f"{YELLOW}[RESEARCH]{RESET} Subtopic {idx}/{total}: {sub}")
        _log_event(log, "SUBTOPIC", f"{idx}/{total} {sub}")
        sub_prompt = f"""Research subtopic: {sub}
User clarifications: {answers}

Instructions:
- Use web research and cite sources (raw URLs).
- Keep it concise: 3-6 bullets.
- Avoid private/local data.
"""
        pass_no = 1
        chunk = _call_codex(
            sub_prompt,
            allow_tools=True,
            label=f"SUB{idx}",
            context=f"{sub} (pass {pass_no})",
            timeout_seconds=sub_timeout,
        )
        if chunk.startswith("[CODEX ERROR]"):
            print(f"{YELLOW}[WARN]{RESET} {chunk}")
            _log_event(log, "WARN", f"{sub}: {chunk}")
            continue
        notes = [chunk]
        sources = _extract_sources(chunk)
        while len(sources) < min_sources:
            need = min_sources - len(sources)
            _log_event(log, "SOURCES", f"{sub}: only {len(sources)}/{min_sources}, fetching {need} more")
            print(f"{YELLOW}[SOURCES]{RESET} {sub}: need {need} more sources")
            pass_no += 1
            src_prompt = f"""Research subtopic: {sub}
User clarifications: {answers}

Instructions:
- Focus only on finding additional sources (raw URLs).
- Provide 2-4 bullets with citations.
- Avoid repeating previously cited URLs.
"""
            extra = _call_codex(
                src_prompt,
                allow_tools=True,
                label=f"SUB{idx}",
                context=f"{sub} (sources {pass_no})",
                timeout_seconds=sub_timeout,
            )
            if extra.startswith("[CODEX ERROR]"):
                _log_event(log, "WARN", f"{sub} sources pass {pass_no}: {extra}")
                break
            notes.append(extra)
            sources = _extract_sources("\n\n".join(notes))
        for _ in range(max_gap_passes):
            gaps = _gap_questions(topic, sub, answers, "\n\n".join(notes))
            if not gaps:
                break
            print(f"{YELLOW}[GAPS]{RESET} " + "; ".join(gaps))
            _log_event(log, "GAPS", f"{sub}: " + "; ".join(gaps))
            pass_no += 1
            follow_prompt = f"""Research subtopic: {sub}
User clarifications: {answers}
Focus questions: {("; ".join(gaps))}

Instructions:
- Use web research and cite sources (raw URLs).
- Keep it concise: 3-6 bullets.
- Avoid private/local data.
"""
            more = _call_codex(
                follow_prompt,
                allow_tools=True,
                label=f"SUB{idx}",
                context=f"{sub} (pass {pass_no})",
                timeout_seconds=sub_timeout,
            )
            if more.startswith("[CODEX ERROR]"):
                print(f"{YELLOW}[WARN]{RESET} {more}")
                _log_event(log, "WARN", f"{sub} pass {pass_no}: {more}")
                break
            notes.append(more)
        parts.append("\n\n".join(notes))

    if not parts:
        return "[CODEX ERROR] No subtopic research completed."

    if checklist_mode:
        print(f"{YELLOW}[CHECKLIST]{RESET} Verifying coverage...")
        _log_event(log, "CHECKLIST", "Verifying coverage")
        missing = _coverage_check(topic, answers, "\n\n".join(parts), checklist_items)
        if missing:
            print(f"{YELLOW}[CHECKLIST]{RESET} Missing: " + "; ".join(missing))
            _log_event(log, "CHECKLIST", "Missing: " + "; ".join(missing))
            for miss in missing:
                print(f"{YELLOW}[RESEARCH]{RESET} Checklist item: {miss}")
                _log_event(log, "CHECKLIST", f"Researching: {miss}")
                miss_prompt = f"""Research topic area: {miss}
User clarifications: {answers}

Instructions:
- Use web research and cite sources (raw URLs).
- Keep it concise: 3-6 bullets.
- Avoid private/local data.
"""
                miss_chunk = _call_codex(
                    miss_prompt,
                    allow_tools=True,
                    label="CHECK",
                    context=miss,
                    timeout_seconds=sub_timeout,
                )
                if miss_chunk.startswith("[CODEX ERROR]"):
                    print(f"{YELLOW}[WARN]{RESET} {miss_chunk}")
                    _log_event(log, "WARN", f"{miss}: {miss_chunk}")
                    continue
                parts.append(miss_chunk)

    print(f"{YELLOW}[SYNTHESIS]{RESET} Combining results...")
    _log_event(log, "SYNTH", "Initial synthesis")
    synth_prompt = f"""Synthesize the following notes into a coherent report.
Include citations as raw URLs. Do not invent sources.

NOTES:
{("\n\n".join(parts))[:12000]}
"""
    synth = _call_codex(
        synth_prompt,
        allow_tools=False,
        label="SYNTH",
        context=topic,
        timeout_seconds=_int_env("TREYS_AGENT_SYNTH_TIMEOUT_SECONDS", 180),
    )
    if synth.startswith("[CODEX ERROR]"):
        return "\n\n".join(parts)

    report = synth
    for pass_no in range(1, review_passes + 1):
        if max_review_questions <= 0:
            break
        questions = _review_questions(topic, answers, report, limit=max_review_questions)
        if not questions:
            break
        print(f"{YELLOW}[REVIEW]{RESET} Pass {pass_no}: " + "; ".join(questions))
        _log_event(log, "REVIEW", f"Pass {pass_no} questions: " + "; ".join(questions))
        for q in questions:
            print(f"{YELLOW}[RESEARCH]{RESET} Review question: {q}")
            _log_event(log, "REVIEW", f"Researching: {q}")
            q_prompt = f"""Research question: {q}
Topic: {topic}
User clarifications: {answers}

Instructions:
- Use web research and cite sources (raw URLs).
- Keep it concise: 3-6 bullets.
- Avoid private/local data.
"""
            q_chunk = _call_codex(
                q_prompt,
                allow_tools=True,
                label=f"REVIEW{pass_no}",
                context=q,
                timeout_seconds=sub_timeout,
            )
            if q_chunk.startswith("[CODEX ERROR]"):
                print(f"{YELLOW}[WARN]{RESET} {q_chunk}")
                _log_event(log, "WARN", f"Review pass {pass_no} {q}: {q_chunk}")
                continue
            parts.append(q_chunk)

        print(f"{YELLOW}[SYNTHESIS]{RESET} Revising report (pass {pass_no})...")
        _log_event(log, "SYNTH", f"Revision pass {pass_no}")
        synth_prompt = f"""Revise the report using the additional notes.
Keep it concise, structured, and include citations as raw URLs.

NOTES:
{("\n\n".join(parts))[:12000]}
"""
        revised = _call_codex(
            synth_prompt,
            allow_tools=False,
            label="SYNTH",
            context=f"{topic} (rev {pass_no})",
            timeout_seconds=_int_env("TREYS_AGENT_SYNTH_TIMEOUT_SECONDS", 180),
        )
        if revised.startswith("[CODEX ERROR]"):
            _log_event(log, "WARN", f"Revision pass {pass_no} failed: {revised}")
            break
        report = revised

    return report


def mode_research(topic: str) -> None:
    print(f"\n{CYAN}[RESEARCH MODE]{RESET} Topic: {topic}")
    print("I'll ask a few quick questions to focus the research.\n")

    log: list[str] = []
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_slug = topic[:32].replace(" ", "_")
    run_dir = BASE_DIR / "research_runs" / f"{run_id}_{run_slug}"
    run_dir.mkdir(parents=True, exist_ok=True)
    profile = _select_research_profile()
    _log_event(log, "PROFILE", profile.get("name", "balanced"))

    questions_prompt = f"""User wants to research: {topic}

Ask 2-3 targeted questions to clarify:
1) what aspect matters most,
2) what it's for (decision, implementation, learning),
3) constraints (time/budget/stack).

Be concise. Output questions only."""

    questions = _call_codex(questions_prompt, allow_tools=False, label="QUESTIONS", context=topic)
    if questions.startswith("[CODEX ERROR]"):
        print(f"{RED}{questions}{RESET}")
        return

    print(f"{CYAN}[QUESTIONS]{RESET}\n{questions}")
    answers = input(f"\n{GREEN}[YOU]{RESET} ").strip()

    topic_label = _short_label(topic)
    if topic_label:
        print(f"\n{YELLOW}[RESEARCHING]{RESET} {topic_label} - gathering sources")
    else:
        print(f"\n{YELLOW}[RESEARCHING]{RESET} Gathering sources and synthesizing...")
    research_prompt = f"""Research topic: {topic}
User clarifications: {answers}

Instructions:
- Do real web research (use shell/python to fetch sources if helpful).
- Compare multiple credible sources.
- Iterate: refine your answer as you discover better sources.
- Return a structured, comprehensive answer.
- Include citations as raw URLs (one per bullet or sentence as needed).
- Do not include any private data from this machine; do not modify files.
"""

    staged = _bool_env("TREYS_AGENT_STAGED_RESEARCH", True)
    if staged:
        findings = _research_staged(topic, answers, profile, log)
    else:
        findings = _call_codex(research_prompt, allow_tools=True, label="RESEARCH", context=topic)
        if findings.startswith("[CODEX ERROR]") and "timed out" in findings.lower():
            print(f"{YELLOW}[INFO]{RESET} Research timed out. Retrying in staged mode...")
            _log_event(log, "WARN", "Initial research timed out; retrying staged")
            findings = _research_staged(topic, answers, profile, log)
    if findings.startswith("[CODEX ERROR]"):
        print(f"{RED}{findings}{RESET}")
        return

    findings_body = findings
    findings_with_sources = _append_sources_section(findings_body)
    print(f"\n{CYAN}[FINDINGS]{RESET}\n{findings_with_sources}")

    while True:
        followup = input(f"\n{GREEN}Follow-up (or 'done'):{RESET} ").strip()
        if not followup or followup.lower() in {"done", "exit", "quit"}:
            break
        _log_event(log, "FOLLOWUP", followup)

        followup_prompt = f"""Topic: {topic}
User clarifications: {answers}

Previous answer:
{findings_body[:4000]}

Follow-up question: {followup}

Do additional research and answer this follow-up. Include citations as raw URLs."""
        more = _call_codex(followup_prompt, allow_tools=True, label="FOLLOWUP", context=followup)
        if more.startswith("[CODEX ERROR]"):
            print(f"{RED}{more}{RESET}")
            continue
        print(f"\n{CYAN}[MORE]{RESET}\n{more}")
        findings_body += f"\n\n{more}"

    save = input(f"\n{YELLOW}Save this research to a file? (y/n):{RESET} ").strip().lower()
    if save != "y":
        log_path = run_dir / "research_log.md"
        log_md = "## Research Log\n" + "\n".join(f"- {e}" for e in log)
        log_path.write_text(log_md, encoding="utf-8")
        print(f"{YELLOW}[LOG]{RESET} Saved research log: {log_path}")
        return

    path = run_dir / "report.md"
    final_report = _append_sources_section(findings_body)
    path.write_text(final_report, encoding="utf-8")
    print(f"{GREEN}[SAVED]{RESET} {path}")
    log_path = run_dir / "research_log.md"
    log_md = "## Research Log\n" + "\n".join(f"- {e}" for e in log)
    log_path.write_text(log_md, encoding="utf-8")
    print(f"{GREEN}[LOG]{RESET} {log_path}")
