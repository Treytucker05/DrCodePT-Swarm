"""
Thin Ollama client used by Trey's Agent.

- Primary model: qwen2.5:7b-instruct
- Fallback model: gemma3:4b
- All calls hit http://127.0.0.1:11434/api/generate with stream=False
- Each helper returns structured dictionaries when possible.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

BASE_URL = "http://127.0.0.1:11434/api/generate"
PRIMARY_MODEL = "qwen2.5:7b-instruct"
FALLBACK_MODEL = "gemma3:4b"
TIMEOUT_SECONDS = 30
MAX_RETRIES = 3

LOG_PATH = Path(__file__).resolve().parents[1] / "logging" / "ollama_calls.log"
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def _log_call(fn: str, model: str, prompt: str, success: bool, latency: float, error: Optional[str] = None):
    entry = {
        "timestamp": time.time(),
        "function": fn,
        "model": model,
        "prompt_preview": prompt[:180],
        "success": success,
        "latency_s": round(latency, 3),
        "error": error,
    }
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    """Best-effort JSON extraction from raw LLM output."""
    if not text:
        return None
    text = text.strip()
    # Strip code fences if present
    if text.startswith("```"):
        parts = text.split("```")
        if len(parts) >= 3:
            text = parts[1].strip()
    try:
        return json.loads(text)
    except Exception:
        return None


def _call_ollama(prompt: str, model: str = PRIMARY_MODEL, **overrides) -> Tuple[bool, str, str]:
    """
    Core call helper.
    Returns (success, model_used, raw_response_text)
    """
    payload = {"model": model, "prompt": prompt, "stream": False}
    payload.update(overrides)

    last_error: Optional[str] = None
    start = time.monotonic()
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.post(BASE_URL, json=payload, timeout=TIMEOUT_SECONDS)
            if resp.status_code == 200:
                data = resp.json()
                raw_text = data.get("response") or data.get("text") or ""
                latency = time.monotonic() - start
                _log_call(overrides.get("call_name", "unspecified"), model, prompt, True, latency, None)
                return True, model, raw_text
            last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
        except Exception as exc:  # pragma: no cover - network
            last_error = str(exc)
        time.sleep(0.6 * attempt)  # simple backoff
    latency = time.monotonic() - start
    _log_call(overrides.get("call_name", "unspecified"), model, prompt, False, latency, last_error)
    return False, model, last_error or ""


def _call_with_fallback(prompt: str, call_name: str, expect_json: bool = True) -> Tuple[Dict[str, Any], str]:
    """
    Call primary model with fallback to gemma. Returns (parsed, model_used).
    """
    success, model_used, raw = _call_ollama(prompt, model=PRIMARY_MODEL, call_name=call_name)
    if not success:
        success, model_used, raw = _call_ollama(prompt, model=FALLBACK_MODEL, call_name=call_name)

    parsed: Dict[str, Any] = {}
    if expect_json:
        parsed = _extract_json(raw) or {}
        if not parsed:
            parsed = {"raw": raw}
    else:
        parsed = {"text": raw}
    parsed.setdefault("model_used", model_used)
    return parsed, model_used


def generate_yaml_plan(goal: str, planner_prompt: str) -> Dict[str, Any]:
    prompt = (
        f"{planner_prompt.strip()}\n\n"
        "User goal:\n"
        f"{goal}\n\n"
        "Return a single YAML plan only. Do not include code fences or commentary."
    )
    data, model_used = _call_with_fallback(prompt, "generate_yaml_plan", expect_json=False)
    return {"plan_yaml": data.get("text") or data.get("raw", ""), "model_used": model_used}


def analyze_failure(task: str, error: str, execution_log: Dict[str, Any]) -> Dict[str, Any]:
    prompt = (
        "You are an expert autonomous agent mechanic. Analyse the failed task and return JSON.\n"
        f"TASK:\n{task}\n\n"
        f"ERROR:\n{error}\n\n"
        f"EXECUTION LOG (compact JSON):\n{json.dumps(execution_log)[:4000]}\n\n"
        "Respond strictly as JSON with keys: analysis, fix_strategy, corrected_yaml, confidence (0-1), is_fixable."
    )
    data, model_used = _call_with_fallback(prompt, "analyze_failure", expect_json=True)
    data.setdefault("model_used", model_used)
    return data


def extract_patterns(task: str, execution_log: Dict[str, Any]) -> Dict[str, Any]:
    prompt = (
        "Summarize reusable patterns from this successful task. Return JSON {patterns:[], recommendations:[], summary}.\n"
        f"TASK GOAL:\n{task}\n\n"
        f"EXECUTION LOG:\n{json.dumps(execution_log)[:3500]}"
    )
    data, model_used = _call_with_fallback(prompt, "extract_patterns", expect_json=True)
    data.setdefault("model_used", model_used)
    return data


def review_code(code: str) -> Dict[str, Any]:
    prompt = (
        "Review this code and suggest improvements. Return JSON with keys "
        "\"improved_code\", \"changes\" (list of strings), and \"explanation\".\n"
        f"CODE:\n{code}"
    )
    data, model_used = _call_with_fallback(prompt, "review_code", expect_json=True)
    data.setdefault("model_used", model_used)
    return data


def summarize_research(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    prompt = (
        "You are a research summarizer. Given multiple sources, produce a concise markdown report.\n"
        "Return JSON with keys: summary_md, key_findings (list), citations (list of {title, url}).\n"
        f"SOURCES:\n{json.dumps(results, indent=2)[:4000]}"
    )
    data, model_used = _call_with_fallback(prompt, "summarize_research", expect_json=True)
    data.setdefault("model_used", model_used)
    return data


__all__ = [
    "generate_yaml_plan",
    "analyze_failure",
    "extract_patterns",
    "review_code",
    "summarize_research",
]
