from __future__ import annotations

"""Local web console & JSON API for DrCodePT Agent.

Run:
    uvicorn agent.console:app --reload --port 8000

Features:
- Serve React UI (built assets in agent/webui/)
- JSON API for tasks, runs, env, handoff, chat
- Legacy HTML helpers kept for compatibility
"""

import html
import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from dotenv import load_dotenv
from fastapi import Body, FastAPI, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from agent.chat_engine import chat_reply

load_dotenv()

AGENT_ROOT = Path(__file__).resolve().parent
TASKS_DIR = AGENT_ROOT / "tasks"
RUNS_DIR = AGENT_ROOT / "runs"
HANDOFF_DIR = AGENT_ROOT / "handoff"
ENV_PATH = AGENT_ROOT / ".env"
WEB_DIST = AGENT_ROOT / "webui"

app = FastAPI(title="DrCodePT Console", version="0.2")


# ----------------- helpers -----------------
def list_tasks() -> List[Path]:
    return sorted(TASKS_DIR.glob("*.yaml"))


def list_runs(limit: int = 10) -> List[Path]:
    runs = [p for p in RUNS_DIR.iterdir() if p.is_dir()]
    runs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return runs[:limit]


def read_summary(run_path: Path) -> str:
    summary = run_path / "summary.md"
    if summary.is_file():
        return summary.read_text(encoding="utf-8")
    return "(no summary yet)"


def tail_events(run_path: Path, n: int = 50) -> List[str]:
    events_file = run_path / "events.jsonl"
    if not events_file.is_file():
        return []
    lines = events_file.read_text(encoding="utf-8").splitlines()
    return lines[-n:]


def set_env(key: str, value: str):
    ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
    entries: Dict[str, str] = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                entries[k.strip()] = v.strip()
    entries[key] = value
    content = "\n".join(f"{k}={v}" for k, v in entries.items()) + "\n"
    ENV_PATH.write_text(content, encoding="utf-8")


def render_page(title: str, body: str) -> HTMLResponse:
    return HTMLResponse(
        f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>{html.escape(title)}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #1a1a1a; }}
    header {{ margin-bottom: 16px; }}
    .card {{ border: 1px solid #ddd; padding: 12px; margin-bottom: 12px; border-radius: 6px; }}
    button {{ padding: 6px 12px; }}
    pre {{ background: #f7f7f7; padding: 8px; overflow-x: auto; }}
    a {{ color: #0b63ce; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>
  <header>
    <h2>DrCodePT Console</h2>
    <nav>
      <a href="/">Home</a> |
      <a href="/runs">Runs</a> |
      <a href="/env">Env</a> |
      <a href="/handoff">Handoff</a>
    </nav>
  </header>
  {body}
</body>
</html>
"""
    )


# ----------------- routes -----------------
@app.get("/", response_class=HTMLResponse)
def home():
    if WEB_DIST.is_dir() and (WEB_DIST / "index.html").is_file():
        return FileResponse(WEB_DIST / "index.html")
    # fallback legacy view
    tasks = list_tasks()
    runs = list_runs(5)
    body = "<h3>Tasks</h3>"
    for t in tasks:
        body += f"""
        <div class="card">
          <strong>{t.name}</strong>
          <form method="post" action="/run" style="display:inline">
            <input type="hidden" name="task" value="{t.name}">
            <button type="submit">Run</button>
          </form>
        </div>
        """
    body += "<h3>Recent Runs</h3>"
    if not runs:
        body += "<p>No runs yet.</p>"
    for r in runs:
        body += f'<div class="card"><a href="/runs/{r.name}">{r.name}</a></div>'
    return render_page("Home", body)


@app.post("/run")
def start_run(task: str = Form(...)):
    task_path = TASKS_DIR / task
    if not task_path.is_file():
        return PlainTextResponse(f"Task not found: {task}", status_code=404)
    # Spawn supervisor as subprocess to avoid blocking
    subprocess.Popen(
        ["python", "-m", "agent.supervisor.supervisor", str(task_path)],
        cwd=AGENT_ROOT.parent,
    )
    return RedirectResponse(url="/runs", status_code=303)


@app.get("/runs", response_class=HTMLResponse)
def runs():
    if WEB_DIST.is_dir() and (WEB_DIST / "index.html").is_file():
        return FileResponse(WEB_DIST / "index.html")
    runs_list = list_runs(20)
    body = "<h3>Runs</h3>"
    if not runs_list:
        body += "<p>No runs yet.</p>"
    for r in runs_list:
        body += f'<div class="card"><a href="/runs/{r.name}">{r.name}</a></div>'
    return render_page("Runs", body)


@app.get("/runs/{run_id}", response_class=HTMLResponse)
def run_detail(run_id: str):
    if WEB_DIST.is_dir() and (WEB_DIST / "index.html").is_file():
        return FileResponse(WEB_DIST / "index.html")
    run_path = RUNS_DIR / run_id
    if not run_path.is_dir():
        return PlainTextResponse("Run not found", status_code=404)
    summary = read_summary(run_path)
    events = tail_events(run_path, 200)
    evidence_dir = run_path / "evidence"
    evidence_links = ""
    if evidence_dir.is_dir():
        for f in evidence_dir.iterdir():
            evidence_links += f'<li><a href="/files/{run_id}/evidence/{f.name}">{f.name}</a></li>'
    body = f"""
    <h3>Run: {run_id}</h3>
    <div class="card">
      <h4>Summary</h4>
      <pre>{html.escape(summary)}</pre>
    </div>
    <div class="card">
      <h4>Evidence</h4>
      <ul>{evidence_links or '<li>(none)</li>'}</ul>
    </div>
    <div class="card">
      <h4>Events (tail)</h4>
      <pre>{html.escape("\\n".join(events))}</pre>
    </div>
    """
    return render_page(run_id, body)


@app.get("/files/{run_id}/evidence/{fname}")
def evidence_file(run_id: str, fname: str):
    path = RUNS_DIR / run_id / "evidence" / fname
    if not path.is_file():
        return PlainTextResponse("File not found", status_code=404)
    return FileResponse(path)


@app.get("/env", response_class=HTMLResponse)
def env_form():
    if WEB_DIST.is_dir() and (WEB_DIST / "index.html").is_file():
        return FileResponse(WEB_DIST / "index.html")
    body = """
    <h3>Update Env</h3>
    <form method="post" action="/env">
      <label>Key <input name="key" required /></label><br/>
      <label>Value <input name="value" required /></label><br/>
      <button type="submit">Save</button>
    </form>
    <p>(Existing secrets are not shown; saving overwrites the key.)</p>
    """
    return render_page("Env", body)


@app.post("/env")
def env_set(key: str = Form(...), value: str = Form(...)):
    set_env(key.strip(), value.strip())
    return RedirectResponse(url="/env", status_code=303)


@app.get("/handoff", response_class=HTMLResponse)
def handoff_view():
    if WEB_DIST.is_dir() and (WEB_DIST / "index.html").is_file():
        return FileResponse(WEB_DIST / "index.html")
    waiting = HANDOFF_DIR / "WAITING.yaml"
    flag = HANDOFF_DIR / "CONTINUE.flag"
    body = "<h3>Handoff</h3>"
    body += f"<p>WAITING present: {'yes' if waiting.exists() else 'no'}</p>"
    body += f"<p>CONTINUE.flag present: {'yes' if flag.exists() else 'no'}</p>"
    body += """
    <form method="post" action="/handoff/continue">
      <button type="submit">Create CONTINUE.flag</button>
    </form>
    """
    if waiting.exists():
        body += "<div class='card'><pre>" + html.escape(waiting.read_text(encoding='utf-8')) + "</pre></div>"
    return render_page("Handoff", body)


@app.post("/handoff/continue")
def handoff_continue():
    HANDOFF_DIR.mkdir(parents=True, exist_ok=True)
    (HANDOFF_DIR / "CONTINUE.flag").write_text("resume", encoding="utf-8")
    return RedirectResponse(url="/handoff", status_code=303)


# -------------- JSON API for React UI --------------


def _task_to_json(path: Path) -> Dict[str, str]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        data = {}
    return {
        "name": path.name.replace(".yaml", ""),
        "type": data.get("type", "unknown"),
        "goal": data.get("goal", ""),
        "yamlContent": path.read_text(encoding="utf-8"),
    }


@app.get("/api/tasks")
def api_get_tasks():
    return [_task_to_json(p) for p in list_tasks()]


def _status_from_summary(summary_text: str) -> str:
    text = summary_text.lower()
    if "run outcome: success" in text:
        return "success"
    if "escalated" in text:
        return "escalated"
    if "abort" in text:
        return "failed"
    if "fail" in text:
        return "failed"
    return "in-progress"


def _run_item_from_dir(run_dir: Path) -> Dict[str, str]:
    summary = (run_dir / "summary.md").read_text(encoding="utf-8") if (run_dir / "summary.md").is_file() else ""
    events = tail_events(run_dir, 1)
    status = _status_from_summary(summary) if summary else ("in-progress" if events else "in-progress")
    started = datetime.fromtimestamp(run_dir.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    return {
        "id": run_dir.name,
        "task": run_dir.name.split("_", 2)[-1] if "_" in run_dir.name else run_dir.name,
        "status": status,
        "startedAt": started,
        "duration": "-",
    }


@app.get("/api/runs")
def api_get_runs():
    runs = [_run_item_from_dir(r) for r in list_runs(100)]
    return runs


def _infer_level(event_name: str) -> str:
    if event_name in ("step_failed", "escalated", "abort"):
        return "ERROR"
    if event_name in ("verify_results", "tool_execute"):
        return "INFO"
    return "DEBUG"


@app.get("/api/runs/{run_id}")
def api_run_details(run_id: str):
    run_path = RUNS_DIR / run_id
    if not run_path.is_dir():
        raise HTTPException(status_code=404, detail="Run not found")
    summary = read_summary(run_path)
    events_raw = tail_events(run_path, 500)
    events = []
    for line in events_raw:
        try:
            data = json.loads(line)
            events.append(
                {
                    "timestamp": data.get("timestamp", ""),
                    "level": _infer_level(data.get("event", "")),
                    "message": f"{data.get('event')}: {data.get('data')}",
                }
            )
        except Exception:
            continue
    evidence_dir = run_path / "evidence"
    evidence = []
    if evidence_dir.is_dir():
        for f in evidence_dir.iterdir():
            ftype = "file"
            if f.suffix.lower() in [".png", ".jpg", ".jpeg"]:
                ftype = "image"
            elif f.suffix.lower() in [".html", ".htm"]:
                ftype = "html"
            evidence.append({"name": f.name, "url": f"/files/{run_id}/evidence/{f.name}", "type": ftype})

    waiting = False
    waiting_file = HANDOFF_DIR / "WAITING.yaml"
    if waiting_file.is_file():
        try:
            content = yaml.safe_load(waiting_file.read_text(encoding="utf-8")) or {}
            waiting = run_id in content.get("run_path", "")
        except Exception:
            waiting = True

    item = _run_item_from_dir(run_path)
    return {
        **item,
        "summary": summary,
        "evidence": evidence,
        "events": events,
        "isWaiting": waiting,
    }


@app.post("/api/run")
def api_run_task(payload: Dict[str, str] = Body(...)):
    task_name = payload.get("task")
    if not task_name:
        raise HTTPException(status_code=400, detail="task required")
    task_path = TASKS_DIR / (task_name if task_name.endswith(".yaml") else f"{task_name}.yaml")
    if not task_path.is_file():
        raise HTTPException(status_code=404, detail="Task not found")

    subprocess.Popen(
        ["python", "-m", "agent.supervisor.supervisor", str(task_path)],
        cwd=AGENT_ROOT.parent,
    )
    # Heuristic: latest run dir matching task after spawn
    run_id = None
    try:
        candidates = [d for d in RUNS_DIR.glob(f"*_{task_name}*")]
        if candidates:
            run_id = sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)[0].name
    except Exception:
        pass
    return {"success": True, "runId": run_id or ""}


@app.get("/api/env/keys")
def api_env_keys():
    keys = set()
    example = AGENT_ROOT / ".env.example"
    if example.is_file():
        for line in example.read_text(encoding="utf-8").splitlines():
            if "=" in line:
                k, _ = line.split("=", 1)
                keys.add(k.strip())
    if ENV_PATH.is_file():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            if "=" in line:
                k, _ = line.split("=", 1)
                keys.add(k.strip())
    return list(sorted(keys))


@app.post("/api/env")
def api_env_set(payload: Dict[str, str] = Body(...)):
    key = payload.get("key")
    value = payload.get("value")
    if not key:
        raise HTTPException(status_code=400, detail="key required")
    set_env(key.strip(), value or "")
    return {"ok": True}


@app.get("/api/handoff")
def api_handoff_state():
    waiting = False
    content = None
    if (HANDOFF_DIR / "WAITING.yaml").is_file():
        waiting = True
        content = (HANDOFF_DIR / "WAITING.yaml").read_text(encoding="utf-8")
    continue_present = (HANDOFF_DIR / "CONTINUE.flag").is_file()
    return {"waiting": waiting, "content": content, "continuePresent": continue_present}


@app.post("/api/handoff/continue")
def api_handoff_continue():
    HANDOFF_DIR.mkdir(parents=True, exist_ok=True)
    (HANDOFF_DIR / "CONTINUE.flag").write_text("resume", encoding="utf-8")
    return {"ok": True}


@app.post("/api/chat")
def api_chat(payload: Dict[str, str] = Body(...)):
    user_msg = (payload.get("message") or "").strip()
    return {"reply": chat_reply(user_msg)}


# -------------- Static files for React UI --------------
if WEB_DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=WEB_DIST / "assets"), name="assets")


@app.get("/{full_path:path}", include_in_schema=False)
def spa_catchall(full_path: str):
    index_file = WEB_DIST / "index.html"
    if index_file.is_file() and not full_path.startswith("api/"):
        return FileResponse(index_file)
    return PlainTextResponse("Not found", status_code=404)
