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
from tempfile import TemporaryDirectory
from datetime import datetime
from contextlib import nullcontext, contextmanager
from urllib.parse import urlparse
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
_CODEX_UNSUPPORTED_FLAGS: set[str] = set()

_SCIENTIFIC_SOURCE_HINTS = {
    "scientific",
    "peer-reviewed",
    "peer reviewed",
    "academic",
    "scholarly",
    "journal",
    "journals",
    "study",
    "studies",
    "systematic review",
    "meta-analysis",
    "clinical trial",
}

_PRIMARY_DOMAINS = [
    "pubmed.ncbi.nlm.nih.gov",
    "pmc.ncbi.nlm.nih.gov",
    "ncbi.nlm.nih.gov",
    "scholar.google.com",
    "nih.gov",
    "cdc.gov",
    "who.int",
    "ama-assn.org",
    "nature.com",
    "science.org",
    "sciencemag.org",
    "cell.com",
    "thelancet.com",
    "nejm.org",
    "jamanetwork.com",
    "bmj.com",
    "pnas.org",
    "annualreviews.org",
    "springer.com",
    "link.springer.com",
    "sciencedirect.com",
    "wiley.com",
    "onlinelibrary.wiley.com",
    "tandfonline.com",
    "academic.oup.com",
    "cambridge.org",
    "ieee.org",
    "ieeexplore.ieee.org",
    "acm.org",
    "dl.acm.org",
    "doi.org",
]

_PREPRINT_DOMAINS = [
    "arxiv.org",
    "biorxiv.org",
    "medrxiv.org",
]

_SECONDARY_DOMAINS = [
    "aamc.org",
    "mededportal.org",
    "acgme.org",
    "health.gov",
    "hhs.gov",
    "medpagetoday.com",
    "statnews.com",
]

_SCIENTIFIC_ALLOWED_SUFFIXES = [
    ".gov",
    ".edu",
    ".mil",
    ".int",
    ".ac.uk",
    ".ac.jp",
    ".ac.in",
    ".ac.nz",
    ".ac.au",
    ".ac.za",
    ".ac.kr",
    ".ac.cn",
    ".ac.id",
]

_ACADEMIC_SUFFIXES = [
    ".edu",
    ".ac.uk",
    ".ac.jp",
    ".ac.in",
    ".ac.nz",
    ".ac.au",
    ".ac.za",
    ".ac.kr",
    ".ac.cn",
    ".ac.id",
]

_BASE_BLOCKED_DOMAINS = [
    "wikipedia.org",
    "wikimedia.org",
]

_MEDIUM_REPUTATION_DOMAINS = [
    "nytimes.com",
    "bbc.com",
    "bbc.co.uk",
    "reuters.com",
    "apnews.com",
    "theguardian.com",
    "washingtonpost.com",
    "economist.com",
    "ft.com",
]

_COMMUNITY_DOMAINS = [
    "reddit.com",
    "quora.com",
    "medium.com",
    "blogspot.com",
    "wordpress.com",
    "substack.com",
    "tumblr.com",
    "facebook.com",
    "x.com",
    "twitter.com",
    "tiktok.com",
    "instagram.com",
    "pinterest.com",
    "fandom.com",
    "answers.com",
    "wikihow.com",
    "stackexchange.com",
    "stackoverflow.com",
]

_MEDICAL_TOPIC_KEYWORDS = {
    "medical",
    "medicine",
    "clinical",
    "patient",
    "med school",
    "medschool",
    "residency",
    "physician",
    "nursing",
    "pharmacy",
    "healthcare",
    "public health",
    "epidemiology",
    "surgery",
    "biomedical",
}

_BLOG_PATH_HINTS = (
    "/blog",
    "/blogs",
    "/forum",
    "/forums",
    "/community",
    "/question",
    "/questions",
    "/answer",
    "/answers",
    "/thread",
    "/threads",
)

_SOURCE_POLICIES: dict[str, dict[str, list[str]]] = {
    "scientific": {
        "allow_domains": [],
        "allow_suffixes": [],
        "block_domains": _BASE_BLOCKED_DOMAINS,
        "block_suffixes": [],
    },
    "reputable": {
        "allow_domains": [],
        "allow_suffixes": [],
        "block_domains": _BASE_BLOCKED_DOMAINS,
        "block_suffixes": [],
    },
}


def _merge_env_list(existing: str | None, additions: list[str]) -> str | None:
    items = {
        item.strip().lower()
        for item in re.split(r"[,\s]+", existing or "")
        if item.strip()
    }
    for item in additions:
        if item:
            items.add(item.strip().lower())
    if not items:
        return None
    return ",".join(sorted(items))


def _select_source_policy(constraints: str | None) -> tuple[str, dict[str, list[str]]]:
    env_policy = (os.getenv("TREYS_AGENT_RESEARCH_SOURCE_POLICY") or "").strip().lower()
    if env_policy in _SOURCE_POLICIES:
        return env_policy, _SOURCE_POLICIES[env_policy]
    lowered = (constraints or "").lower()
    if any(hint in lowered for hint in _SCIENTIFIC_SOURCE_HINTS):
        return "scientific", _SOURCE_POLICIES["scientific"]
    return "reputable", _SOURCE_POLICIES["reputable"]


def _policy_env_overrides(policy: dict[str, list[str]]) -> dict[str, str | None]:
    return {
        "TREYS_AGENT_WEB_ALLOWLIST": _merge_env_list(
            os.getenv("TREYS_AGENT_WEB_ALLOWLIST"), policy.get("allow_domains", [])
        ),
        "TREYS_AGENT_WEB_ALLOW_SUFFIXES": _merge_env_list(
            os.getenv("TREYS_AGENT_WEB_ALLOW_SUFFIXES"), policy.get("allow_suffixes", [])
        ),
        "TREYS_AGENT_WEB_BLOCKLIST": _merge_env_list(
            os.getenv("TREYS_AGENT_WEB_BLOCKLIST"), policy.get("block_domains", [])
        ),
        "TREYS_AGENT_WEB_BLOCK_SUFFIXES": _merge_env_list(
            os.getenv("TREYS_AGENT_WEB_BLOCK_SUFFIXES"), policy.get("block_suffixes", [])
        ),
    }


@contextmanager
def _temporary_env(overrides: dict[str, str | None]):
    previous = {key: os.environ.get(key) for key in overrides}
    for key, value in overrides.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
    try:
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _normalize_host(url: str) -> str:
    if not url:
        return ""
    try:
        host = urlparse(url).netloc or ""
    except Exception:
        host = ""
    host = host.lower().strip()
    if host.startswith("www."):
        host = host[4:]
    if ":" in host:
        host = host.split(":", 1)[0]
    return host.strip(".")


def _host_matches(host: str, domain: str) -> bool:
    if not host or not domain:
        return False
    return host == domain or host.endswith("." + domain)


def _host_in_list(host: str, domains: list[str]) -> bool:
    for domain in domains:
        if _host_matches(host, domain):
            return True
    return False


def _is_medical_topic(topic: str, constraints: str | None) -> bool:
    blob = f"{topic} {constraints or ''}".lower()
    return any(keyword in blob for keyword in _MEDICAL_TOPIC_KEYWORDS)


def _classify_source(item: dict, *, medical: bool) -> dict:
    url = (item or {}).get("url") or ""
    title = ((item or {}).get("title") or "").lower()
    snippet = ((item or {}).get("snippet") or "").lower()
    host = _normalize_host(url)
    if not host:
        return {"tier": "low", "score": -10, "preprint": False}

    if _host_in_list(host, _COMMUNITY_DOMAINS):
        return {"tier": "community", "score": 20, "preprint": False}

    parsed = urlparse(url)
    path = (parsed.path or "").lower()

    preprint = _host_in_list(host, _PREPRINT_DOMAINS)
    if _host_in_list(host, _PRIMARY_DOMAINS):
        tier = "primary"
        score = 90
    elif preprint:
        tier = "secondary"
        score = 60
    elif _host_in_list(host, _SECONDARY_DOMAINS):
        tier = "secondary"
        score = 70
    elif _host_in_list(host, _MEDIUM_REPUTATION_DOMAINS):
        tier = "secondary"
        score = 55
    else:
        if host.endswith(".edu") or any(host.endswith(suffix) for suffix in _ACADEMIC_SUFFIXES):
            if any(token in path for token in ("/research", "/publications", "/repository", "/scholar", "/lab", "/labs")):
                tier = "primary"
                score = 80
            elif medical and any(token in path for token in ("/medicine", "/medical", "/med", "/health")):
                tier = "secondary"
                score = 60
            else:
                tier = "secondary"
                score = 50
        elif host.endswith(".gov") or host.endswith(".int") or host.endswith(".mil"):
            if medical or "health" in host or "/health" in path:
                tier = "secondary"
                score = 60
            else:
                tier = "secondary"
                score = 50
        elif host.startswith("docs.") or "/docs" in path or "documentation" in url:
            tier = "secondary"
            score = 50
        else:
            tier = "low"
            score = 5

    if tier != "low" and any(tag in path for tag in _BLOG_PATH_HINTS):
        if _host_in_list(host, _PRIMARY_DOMAINS) or _host_in_list(host, _SECONDARY_DOMAINS):
            score -= 10
        else:
            tier = "low"
            score = 5

    if tier != "low" and ("journal" in host or "journal" in title or "journal" in snippet):
        score += 2
    if tier != "low" and "doi.org" in host:
        score += 2

    return {"tier": tier, "score": score, "preprint": preprint}


def _short_label(text: str, *, max_words: int = 6, max_chars: int = 40) -> str:
    words = re.findall(r"\S+", text or "")
    if not words:
        return ""
    label = " ".join(words[:max_words])
    if len(label) > max_chars:
        label = label[: max_chars - 3].rstrip() + "..."
    return label


_CODEX_CONFIG_CACHE: dict | None = None


def _load_codex_config() -> dict:
    global _CODEX_CONFIG_CACHE
    if _CODEX_CONFIG_CACHE is not None:
        return _CODEX_CONFIG_CACHE
    path = Path.home() / ".codex" / "config.toml"
    if not path.is_file():
        _CODEX_CONFIG_CACHE = {}
        return _CODEX_CONFIG_CACHE
    raw = ""
    try:
        raw = path.read_text(encoding="utf-8", errors="ignore")
        try:
            import tomllib  # type: ignore

            _CODEX_CONFIG_CACHE = tomllib.loads(raw)
            return _CODEX_CONFIG_CACHE or {}
        except Exception:
            pass
    except Exception:
        _CODEX_CONFIG_CACHE = {}
        return _CODEX_CONFIG_CACHE

    cfg: dict[str, str] = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("["):
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key in {"model", "model_reasoning_effort"}:
            cfg[key] = value
    _CODEX_CONFIG_CACHE = cfg
    return _CODEX_CONFIG_CACHE


def _normalize_effort(value: str) -> str:
    effort = (value or "").strip().lower()
    if effort in {"xhigh", "extra_high", "xh"}:
        return "high"
    if effort in {"xlow", "extra_low", "xl"}:
        return "low"
    if effort in {"high", "medium", "low"}:
        return effort
    return "medium"


def _debug_agent_banner(agent_label: str) -> None:
    cfg = _load_codex_config() or {}
    profiles = cfg.get("profiles") if isinstance(cfg.get("profiles"), dict) else {}
    profile_name = (os.getenv("CODEX_PROFILE_REASON") or "reason").strip()
    profile_cfg = profiles.get(profile_name, {}) if isinstance(profiles, dict) else {}
    model = (os.getenv("CODEX_MODEL") or profile_cfg.get("model") or cfg.get("model") or "default").strip()
    effort_raw = os.getenv("CODEX_REASONING_EFFORT") or profile_cfg.get("model_reasoning_effort") or cfg.get("model_reasoning_effort") or "medium"
    effort = _normalize_effort(str(effort_raw))
    print(f"[MODEL: {model} | EFFORT: {effort} | AGENT: {agent_label}]")


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


def _build_sources_block(sources: list[dict], *, max_chars: int = 8000) -> str:
    lines: list[str] = []
    total = 0
    for idx, src in enumerate(sources, 1):
        title = src.get("title") or "Untitled"
        url = src.get("url") or ""
        snippet = src.get("snippet") or ""
        excerpt = src.get("excerpt") or ""
        block = f"[{idx}] {title}\nURL: {url}\nSnippet: {snippet}\nExcerpt: {excerpt}\n"
        if total + len(block) > max_chars:
            break
        lines.append(block)
        total += len(block)
    return "\n".join(lines).strip()


def _research_agent_sources(
    topic: str,
    ctx: "RunContext",
    *,
    constraints: str | None = None,
    max_results: int = 15,
) -> list[dict]:
    from agent.autonomous.tools.builtins import WebFetchArgs, WebSearchArgs, web_fetch, web_search

    base_query = topic.strip()
    if constraints:
        base_query = f"{base_query} {constraints}".strip()

    def _search(query: str) -> list[dict]:
        search = web_search(ctx, WebSearchArgs(query=query, max_results=max_results))
        if not search.success:
            return []
        output = search.output or {}
        return output.get("results") or []

    def _dedupe(items: list[dict]) -> list[dict]:
        seen: set[str] = set()
        unique: list[dict] = []
        for item in items:
            url = (item or {}).get("url") or ""
            title = (item or {}).get("title") or ""
            host = _normalize_host(url)
            key = url or f"{host}|{title}"
            if key in seen:
                continue
            seen.add(key)
            unique.append(item)
        return unique

    def _rank(
        items: list[dict], *, medical: bool
    ) -> tuple[
        list[tuple[int, int, dict]],
        list[tuple[int, int, dict]],
        list[tuple[int, int, dict]],
        list[tuple[int, int, dict]],
    ]:
        primary: list[tuple[int, int, dict]] = []
        secondary: list[tuple[int, int, dict]] = []
        community: list[tuple[int, int, dict]] = []
        low: list[tuple[int, int, dict]] = []
        for idx, item in enumerate(items):
            info = _classify_source(item or {}, medical=medical)
            entry = (int(info["score"]), idx, {**(item or {}), "_tier": info["tier"], "_preprint": info["preprint"]})
            if info["tier"] == "primary":
                primary.append(entry)
            elif info["tier"] == "secondary":
                secondary.append(entry)
            elif info["tier"] == "community":
                community.append(entry)
            else:
                low.append(entry)
        primary.sort(key=lambda row: (-row[0], row[1]))
        secondary.sort(key=lambda row: (-row[0], row[1]))
        community.sort(key=lambda row: (-row[0], row[1]))
        low.sort(key=lambda row: (-row[0], row[1]))
        return primary, secondary, community, low

    is_medical = _is_medical_topic(topic, constraints)

    primary_query = f"{base_query} \"peer reviewed\" OR pubmed OR study".strip()
    results = _search(primary_query)
    results = _dedupe(results)

    primary, secondary, community, low = _rank(results, medical=is_medical)

    if len(primary) < 5:
        if is_medical:
            secondary_hint = (
                "preprint OR medrxiv OR biorxiv OR arxiv OR AAMC OR MedEdPORTAL OR "
                "medical education OR med school OR residency"
            )
        else:
            secondary_hint = "preprint OR arxiv OR biorxiv OR medrxiv OR report OR guideline"
        secondary_query = f"{base_query} {secondary_hint}".strip()
        more = _search(secondary_query)
        if more:
            results = _dedupe(results + more)
            primary, secondary, community, low = _rank(results, medical=is_medical)

    selected_entries: list[tuple[int, int, dict]] = []
    if len(primary) >= 5:
        selected_entries = primary[:5]
    else:
        need = 5 - len(primary)
        selected_entries = primary + secondary[:max(0, need)]
        if len(selected_entries) < 5:
            need = 5 - len(selected_entries)
            selected_entries += community[:max(0, need)]
        if len(selected_entries) < 5:
            need = 5 - len(selected_entries)
            selected_entries += low[:max(0, need)]

    if len(selected_entries) < 3:
        print(f"{YELLOW}[WARN]{RESET} Insufficient sources found (need >=3).")
        return []

    sources: list[dict] = []
    for _, _, item in selected_entries:
        title = (item or {}).get("title") or "Untitled"
        url = (item or {}).get("url") or ""
        snippet = (item or {}).get("snippet") or ""
        if item.get("_preprint"):
            note = "Preprint (not peer-reviewed)."
            snippet = f"{snippet} NOTE: {note}".strip()
        excerpt = ""
        if url:
            fetched = web_fetch(ctx, WebFetchArgs(url=url, strip_html=True))
            if fetched.success:
                text = (fetched.output or {}).get("text") or ""
                excerpt = text.strip()[:1500]
        sources.append(
            {
                "title": title,
                "url": url,
                "snippet": snippet,
                "excerpt": excerpt,
            }
        )
    return sources


def _analysis_agent(topic: str, sources: list[dict], *, constraints: str | None = None) -> str:
    sources_block = _build_sources_block(sources)
    constraints_block = f"User constraints: {constraints}\n" if constraints else ""
    prompt = f"""You are the Analysis Agent.
Topic: {topic}
{constraints_block}

Use ONLY the sources below. Extract key findings with citations (raw URLs).
If a source is marked as a preprint (not peer-reviewed), call that out.
Return bullets under headings:
- Key Findings
- Evidence Gaps (if any)

Sources:
{sources_block}
"""
    return _call_codex(prompt, allow_tools=False, label="ANALYSIS", context=topic)


def _synthesis_agent(
    topic: str, sources: list[dict], analysis: str, *, constraints: str | None = None
) -> str:
    sources_block = _build_sources_block(sources)
    constraints_block = f"User constraints: {constraints}\n" if constraints else ""
    prompt = f"""You are the Synthesis Agent.
Topic: {topic}
{constraints_block}

Combine the analysis into a comprehensive, actionable report.
Include sections:
1) Executive Summary
2) Key Findings (with citations)
3) Recommendations (actionable)
4) Sources (raw URLs)
If any sources are preprints, label them as not peer-reviewed.

Analysis:
{analysis[:6000]}

Sources:
{sources_block}
"""
    return _call_codex(prompt, allow_tools=False, label="SYNTHESIS", context=topic)


def _has_citations(text: str) -> bool:
    lowered = text.lower()
    return "http://" in lowered or "https://" in lowered


def _log_event(log: list[str], kind: str, message: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    log.append(f"{ts} [{kind}] {message}")


def _select_research_profile() -> dict:
    def _normalize_choice(raw: str) -> str:
        tokens = re.findall(r"[a-z0-9]+", (raw or "").lower())
        if not tokens:
            return ""
        for key in ("1", "2", "3", "4", "light", "balanced", "moderate", "deep", "checklist", "l", "b", "m", "d", "c"):
            if key in tokens:
                return key
        return tokens[0]

    profiles = {
        "1": {
            "name": "light",
            "max_gap_passes": 0,
            "min_subtopics": 3,
            "max_subtopics": 3,
            "checklist": False,
            "review_passes": 0,
            "max_review_questions": 0,
            "min_sources_per_subtopic": 1,
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

    env_choice = _normalize_choice(os.getenv("TREYS_AGENT_RESEARCH_MODE"))
    if env_choice:
        choice_key = aliases.get(env_choice, env_choice)
        profile = profiles.get(choice_key)
        if profile:
            print(f"{YELLOW}[DEPTH]{RESET} {profile['name']} (from TREYS_AGENT_RESEARCH_MODE)")
            return profile

    print(
        f"{YELLOW}[DEPTH]{RESET} Choose research depth:\n"
        "  1) Light     (0 self-check passes)\n"
        "  2) Balanced  (1-2 self-check passes)\n"
        "  3) Deep      (up to 5 self-check passes)\n"
        "  4) Checklist (>=5 subtopics + coverage checklist)\n"
    )
    choice = _normalize_choice(input(f"{GREEN}Select 1-4 (default 2):{RESET} "))
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
    retry_on_unknown_feature: bool = True,
) -> str:
    show_progress = _bool_env("TREYS_AGENT_PROGRESS", True) if show_progress is None else show_progress
    use_json_events = _bool_env("TREYS_AGENT_JSON_EVENTS", True) if show_progress else False
    heartbeat_seconds = _int_env("TREYS_AGENT_HEARTBEAT_SECONDS", 20)
    context_label = _short_label(context or "")

    def _error(reason: str) -> str:
        msg = f"{label} failed: {reason}"
        print(f"{RED}[ERROR]{RESET} {msg}")
        return f"[CODEX ERROR] {msg}"

    # Note: `--search` is a global flag (must appear before the `exec` subcommand).
    cmd: list[str] = _codex_command() + [
        "--profile",
        "research",
        "--dangerously-bypass-approvals-and-sandbox",
    ]
    if allow_tools:
        cmd += ["--search"]
    cmd += ["exec", "--skip-git-repo-check"]
    if use_json_events:
        cmd += ["--json"]
    if not allow_tools:
        cmd += ["--disable", "shell_tool"]
    if "rmcp_client" not in _CODEX_UNSUPPORTED_FLAGS:
        cmd += ["--disable", "rmcp_client"]

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
            return _error("Codex CLI not found on PATH")
        except subprocess.TimeoutExpired:
            timeout_s = timeout_seconds or int(os.getenv("CODEX_TIMEOUT_SECONDS", "600"))
            return _error(f"timed out after {timeout_s}s")

        if proc.returncode != 0:
            error = proc.stderr.strip() if proc.stderr else "Unknown error"
            if (
                retry_on_unknown_feature
                and "Unknown feature flag: rmcp_client" in error
            ):
                _CODEX_UNSUPPORTED_FLAGS.add("rmcp_client")
                return _call_codex(
                    prompt,
                    allow_tools=allow_tools,
                    label=label,
                    context=context,
                    timeout_seconds=timeout_seconds,
                    show_progress=show_progress,
                    retry_on_unknown_feature=False,
                )
            return _error(error)

        return proc.stdout.strip() if proc.stdout else ""

    # Progress / event mode (non-interactive; parse output after completion).
    timeout_s = timeout_seconds or int(os.getenv("CODEX_TIMEOUT_SECONDS", "600"))
    final_parts: list[str] = []

    def _status(msg: str) -> None:
        if context_label:
            msg = f"{msg} ({context_label})"
        if msg:
            print(f"{YELLOW}[{label}]{RESET} {msg}")

    progress_stop: threading.Event | None = None
    progress_thread: threading.Thread | None = None

    def _start_progress() -> None:
        nonlocal progress_stop, progress_thread
        if not sys.stdout.isatty():
            return
        progress_stop = threading.Event()
        start_time = time.time()
        bar_width = 20

        def _run() -> None:
            frames = ["|", "/", "-", "\\"]
            idx = 0
            while not progress_stop.wait(0.2):
                elapsed = int(time.time() - start_time)
                if timeout_s:
                    pct = min(1.0, elapsed / max(1, timeout_s))
                    filled = int(pct * bar_width)
                    bar = "#" * filled + "-" * (bar_width - filled)
                    msg = f"\r[{label}] {frames[idx]} [{bar}] {int(pct * 100):3d}% {elapsed:>3}s"
                else:
                    msg = f"\r[{label}] {frames[idx]} {elapsed:>3}s"
                try:
                    sys.stdout.write(msg)
                    sys.stdout.flush()
                except Exception:
                    pass
                idx = (idx + 1) % len(frames)
            try:
                sys.stdout.write("\r" + (" " * 80) + "\r")
                sys.stdout.flush()
            except Exception:
                pass

        progress_thread = threading.Thread(target=_run, daemon=True)
        progress_thread.start()

    def _stop_progress() -> None:
        if progress_stop:
            progress_stop.set()
        if progress_thread:
            progress_thread.join(timeout=1)

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

    _start_progress()
    try:
        proc = subprocess.run(
            cmd,
            input=prompt,
            text=True,
            encoding="utf-8",
            errors="ignore",
            capture_output=True,
            env=env,
            cwd=str(REPO_ROOT),
            timeout=timeout_s,
        )
    except FileNotFoundError:
        _stop_progress()
        return _error("Codex CLI not found on PATH")
    except subprocess.TimeoutExpired:
        _stop_progress()
        return _error(f"timed out after {timeout_s}s")
    finally:
        _stop_progress()

    if proc.returncode != 0:
        err = proc.stderr.strip() if proc.stderr else "Unknown error"
        if (
            retry_on_unknown_feature
            and "Unknown feature flag: rmcp_client" in err
        ):
            _CODEX_UNSUPPORTED_FLAGS.add("rmcp_client")
            return _call_codex(
                prompt,
                allow_tools=allow_tools,
                label=label,
                context=context,
                timeout_seconds=timeout_seconds,
                show_progress=show_progress,
                retry_on_unknown_feature=False,
            )
        return _error(err)

    stdout_text = proc.stdout or ""
    if use_json_events:
        for line in stdout_text.splitlines():
            try:
                obj = json.loads(line.strip())
            except Exception:
                continue
            if isinstance(obj, dict):
                _handle_json_event(obj)
        if final_parts:
            return "\n".join(final_parts).strip()
    return stdout_text.strip()


def _research_staged(topic: str, answers: str, profile: dict, log: list[str]) -> str:
    min_subtopics = int(profile.get("min_subtopics") or 3)
    max_subtopics = int(profile.get("max_subtopics") or max(min_subtopics, 5))
    if max_subtopics < min_subtopics:
        max_subtopics = min_subtopics
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

Return {min_subtopics}-{max_subtopics} focused subtopics as bullet points. Output only bullets."""
    if checklist_mode:
        plan_prompt += "\nEnsure coverage of: " + "; ".join(checklist_items)
    _log_event(log, "PLAN", f"Generating subtopics (min {min_subtopics})")
    plan_text = _call_codex(plan_prompt, allow_tools=False, label="PLAN", context=topic)
    if plan_text.startswith("[CODEX ERROR]"):
        _log_event(log, "ERROR", plan_text)
        return plan_text

    subtopics = _extract_bullets(plan_text, limit=max_subtopics)
    if len(subtopics) < min_subtopics:
        expand_prompt = f"""We need at least {min_subtopics} unique subtopics.
Current list:
{chr(10).join(f"- {s}" for s in subtopics)}

Add more unique subtopics to reach {min_subtopics}. Output bullets only."""
        extra = _call_codex(expand_prompt, allow_tools=False, label="PLAN", context=topic)
        if not extra.startswith("[CODEX ERROR]"):
            subtopics.extend(_extract_bullets(extra, limit=max_subtopics))
        seen = set()
        subtopics = [s for s in subtopics if not (s.lower() in seen or seen.add(s.lower()))]
    if len(subtopics) > max_subtopics:
        subtopics = subtopics[:max_subtopics]
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
    notes_blob = "\n\n".join(parts)
    synth_prompt = (
        "Synthesize the following notes into a coherent report.\n"
        "Include citations as raw URLs. Do not invent sources.\n"
        "\n"
        "NOTES:\n"
        f"{notes_blob[:12000]}\n"
    )
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


def mode_research(topic: str, *, constraints: str | None = None) -> None:
    print(f"\n{CYAN}[RESEARCH MODE]{RESET} Topic: {topic}")
    print(f"{CYAN}[SPAWN]{RESET} Research Agent, Analysis Agent, Synthesis Agent\n")
    if constraints:
        print(f"{YELLOW}[CONSTRAINTS]{RESET} {constraints}")

    from agent.autonomous.config import RunContext

    with TemporaryDirectory(prefix="research_multi_") as tmp_dir:
        run_dir = Path(tmp_dir)
        ctx = RunContext(
            run_id="manual",
            run_dir=run_dir,
            workspace_dir=run_dir,
            profile=None,
            usage=None,
        )

        policy_name, policy = _select_source_policy(constraints)
        overrides = _policy_env_overrides(policy)
        with _temporary_env(overrides):
            _debug_agent_banner("Research")
            print(f"{YELLOW}[RESEARCH AGENT]{RESET} Gathering sources...")
            sources = _research_agent_sources(topic, ctx, constraints=constraints)
            if not sources:
                print(f"{RED}[ERROR]{RESET} No sources found under the current source policy.")
                print(
                    f"{YELLOW}[INFO]{RESET} Policy: {policy_name}. "
                    "Adjust allowlists via TREYS_AGENT_RESEARCH_SOURCE_POLICY or "
                    "TREYS_AGENT_WEB_ALLOWLIST/TREYS_AGENT_WEB_ALLOW_SUFFIXES."
                )
                return

            _debug_agent_banner("Analysis")
            print(f"{YELLOW}[ANALYSIS AGENT]{RESET} Extracting key findings...")
            analysis = _analysis_agent(topic, sources, constraints=constraints)
            if analysis.startswith("[CODEX ERROR]"):
                print(f"{RED}{analysis}{RESET}")
                return

            _debug_agent_banner("Synthesis")
            print(f"{YELLOW}[SYNTHESIS AGENT]{RESET} Producing report...")
            report = _synthesis_agent(topic, sources, analysis, constraints=constraints)
            if report.startswith("[CODEX ERROR]"):
                print(f"{RED}{report}{RESET}")
                return

    print(f"\n{CYAN}[REPORT]{RESET}\n{report}")
