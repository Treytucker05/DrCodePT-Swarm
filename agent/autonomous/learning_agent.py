"""
Learning Agent - The autonomous, self-learning orchestrator.

This is the brain that ties everything together:
1. Receives a user request
2. Uses LLM to parse intent and identify what's needed
3. Checks local credentials/skills first
4. If unknown, researches how to do it using proper web search
5. Uses LLM to create a detailed plan
6. Opens browser FIRST, then executes with vision-guided automation
7. Saves everything - credentials, skills, errors
8. Learns from success/failure

The LLM is used for:
- Understanding the user's intent (not hardcoded pattern matching)
- Generating search queries
- Creating step-by-step plans
- Analyzing research results
- Vision-guided execution

Inspired by Voyager, AutoGPT, and Claude Computer Use.
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import tempfile
import time
import webbrowser
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Literal
from urllib.parse import urlparse
from uuid import uuid4

from pydantic import BaseModel, Field
try:
    from pydantic import ConfigDict
except Exception:
    ConfigDict = None

from agent.llm.json_enforcer import build_repair_prompt, enforce_json_response

# Load .env file for API keys
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CREDENTIALS_DIR = Path.home() / ".google_credentials"

# Ensure .env is loaded from repo root
_env_path = REPO_ROOT / ".env"
if _env_path.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_path)
    except ImportError:
        # Manual .env loading if python-dotenv not available
        import os
        with open(_env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())

# JSON Schema for intent parsing
INTENT_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "description": "The action to perform (e.g., calendar.list_events, send_email, create_event)"
        },
        "service": {
            "type": "string",
            "description": "The service needed (e.g., google_calendar, outlook, gmail)"
        },
        "auth_provider": {
            "type": "string",
            "description": "Authentication provider (google, microsoft, or null)"
        },
        "needs_auth": {
            "type": "boolean",
            "description": "Whether authentication is required"
        },
        "parameters": {
            "type": "object",
            "description": "Extracted parameters like time_range, recipient, subject"
        },
        "clarifying_questions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Questions to ask the user if intent is unclear"
        },
        "confidence": {
            "type": "number",
            "description": "Confidence in the interpretation (0-1)"
        }
    },
    "required": ["action", "needs_auth", "confidence"]
}

# JSON Schema for plan generation
PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "plan_type": {
            "type": "string",
            "enum": ["EXECUTE", "SETUP_GUIDE"],
            "description": "EXECUTE for automation, SETUP_GUIDE for manual setup instructions"
        },
        "summary": {
            "type": "string",
            "description": "Brief summary of the plan"
        },
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "phase": {"type": "string", "enum": ["SETUP", "EXECUTE", "VERIFY"]},
                    "description": {"type": "string"},
                    "action": {"type": "string", "enum": ["open_browser", "vision_guided", "api_call", "wait", "manual"]},
                    "url": {"type": "string"},
                    "details": {"type": "string"}
                },
                "required": ["phase", "description", "action"]
            }
        },
        "estimated_time": {
            "type": "string",
            "description": "Rough time estimate"
        },
        "risks": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Potential issues to watch for"
        }
    },
    "required": ["plan_type", "summary", "steps"]
}

# JSON Schema for research synthesis
RESEARCH_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "summary": {"type": "string"},
        "setup_steps": {"type": "array", "items": {"type": "string"}},
        "execution_steps": {"type": "array", "items": {"type": "string"}},
        "success_checks": {"type": "array", "items": {"type": "string"}},
        "caveats": {"type": "array", "items": {"type": "string"}},
        "sources": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["summary", "sources"],
}


class TaskResult(BaseModel):
    """Result of executing a task."""
    success: bool
    summary: str
    steps_taken: int = 0
    skill_used: Optional[str] = None
    skill_learned: Optional[str] = None
    research_performed: bool = False
    error: Optional[str] = None
    evidence: Dict[str, Any] = Field(default_factory=dict)


class ParsedIntent(BaseModel):
    """Parsed user intent."""
    action: str  # e.g., "calendar.list_events", "send_email", "search_web"
    service: Optional[str] = None  # e.g., "google_calendar", "outlook", "gmail"
    parameters: Dict[str, Any] = Field(default_factory=dict)
    needs_auth: bool = False
    auth_provider: Optional[str] = None  # "google", "microsoft"
    clarifying_questions: List[str] = Field(default_factory=list)


class IntentPayload(BaseModel):
    """Strict intent payload expected from the LLM."""
    action: str
    service: Optional[str] = None
    auth_provider: Optional[str] = None
    needs_auth: bool
    parameters: Dict[str, Any] = Field(default_factory=dict)
    clarifying_questions: List[str] = Field(default_factory=list)
    confidence: Optional[float] = None

    if ConfigDict:
        model_config = ConfigDict(extra="forbid")
    else:
        class Config:
            extra = "forbid"


class PlanStepPayload(BaseModel):
    phase: Literal["SETUP", "EXECUTE", "VERIFY"]
    description: str
    action: Literal["open_browser", "vision_guided", "api_call", "wait", "manual"]
    url: Optional[str] = None
    details: Optional[str] = None

    if ConfigDict:
        model_config = ConfigDict(extra="forbid")
    else:
        class Config:
            extra = "forbid"


class PlanPayload(BaseModel):
    plan_type: Literal["EXECUTE", "SETUP_GUIDE"] = "EXECUTE"
    summary: str
    steps: List[PlanStepPayload] = Field(default_factory=list)
    estimated_time: Optional[str] = None
    risks: List[str] = Field(default_factory=list)

    if ConfigDict:
        model_config = ConfigDict(extra="forbid")
    else:
        class Config:
            extra = "forbid"


class ResearchPayload(BaseModel):
    summary: str
    setup_steps: List[str] = Field(default_factory=list)
    execution_steps: List[str] = Field(default_factory=list)
    success_checks: List[str] = Field(default_factory=list)
    caveats: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)

    if ConfigDict:
        model_config = ConfigDict(extra="forbid")
    else:
        class Config:
            extra = "forbid"


class ExecutionPlan(BaseModel):
    """Plan for executing a task."""
    request: str
    intent: ParsedIntent
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    research_summary: Optional[str] = None
    approved: bool = False
    plan_type: str = "EXECUTE"


class LearningAgent:
    """
    Autonomous agent that learns new skills from experience.

    The CORRECT flow:
    1. User request → Parse intent, ask clarifying questions
    2. Check local credentials/skills first
    3. If not found → Research with proper web search (not PowerShell)
    4. Build plan → Show to user → Get approval
    5. Open browser FIRST (so vision can see it)
    6. Execute with vision-guided automation
    7. On success → Save credentials, save skill
    8. On failure → Log to reflexion, learn
    """

    def __init__(self, llm=None):
        self.llm = llm
        self.skill_library = None
        self.vision_executor = None
        self.memory_store = None
        self._initialized = False
        self._disable_codex = False

        # Callbacks
        self.on_status: Optional[Callable[[str], None]] = None
        self.on_user_input: Optional[Callable[[str], str]] = None

    def initialize(self) -> None:
        """Initialize all components."""
        if self._initialized:
            return

        # Skill library
        from agent.autonomous.skill_library import get_skill_library
        self.skill_library = get_skill_library()
        self.skill_library.initialize()

        # Hybrid executor (UI automation + vision fallback)
        # This is the NEW architecture - much more accurate than vision-only
        try:
            from agent.autonomous.hybrid_executor import get_hybrid_executor
            self.executor = get_hybrid_executor(self.llm)
            self.executor.initialize()
            self._status("Using hybrid executor (UI automation + vision fallback)")
        except Exception as e:
            # Fall back to vision-only if hybrid fails
            logger.warning(f"Hybrid executor failed, using vision-only: {e}")
            from agent.autonomous.vision_executor import get_vision_executor
            self.executor = get_vision_executor(self.llm)
            self.executor.initialize()

        # Keep reference for backwards compatibility
        self.vision_executor = self.executor

        # Memory store (for reflexion)
        try:
            from agent.autonomous.memory.sqlite_store import SqliteMemoryStore  
            memory_path = os.getenv("AGENT_MEMORY_DB") or ""
            if memory_path:
                memory_path = Path(memory_path)
            else:
                memory_path = REPO_ROOT / "agent" / "memory" / "autonomous_memory.sqlite3"
            memory_path.parent.mkdir(parents=True, exist_ok=True)
            self.memory_store = SqliteMemoryStore(path=str(memory_path))        
        except Exception as e:
            logger.debug(f"Could not initialize memory store: {e}")
            self.memory_store = None

        self._initialized = True
        self._status("Learning agent initialized")

    def _status(self, message: str) -> None:
        """Report status."""
        logger.info(message)
        if self.on_status:
            self.on_status(message)

    def _ask_user(self, question: str) -> str:
        """Ask the user a question."""
        if os.getenv("AGENT_AUTO_ANSWER", "").strip().lower() in {"1", "true", "yes", "y", "on"}:
            return self._auto_answer(question)
        if self.on_user_input:
            return self.on_user_input(question)
        else:
            print(f"\n  [AGENT ASKS] {question}")
            return input("  > ").strip()

    def _auto_answer(self, question: str) -> str:
        """Auto-answer common prompts for hands-off runs."""
        q = (question or "").strip().lower()
        auto_approve = os.getenv("AGENT_AUTO_APPROVE", "").strip().lower() in {"1", "true", "yes", "y", "on"}
        if "execute this plan" in q or "do you want me to execute" in q:
            return "yes" if auto_approve else "no"
        if "are you referring to" in q and "notepad" in q:
            return "yes"
        if "motivational message" in q or ("what" in q and "message" in q):
            return "make it up"
        if "yes/no" in q:
            return "yes" if auto_approve else "no"
        # Default to yes for autonomy
        return "yes"

    def _looks_sensitive(self, text: str) -> bool:
        """Best-effort detection of sensitive user input to avoid storing secrets."""
        if not text:
            return False
        lowered = text.lower()
        if any(k in lowered for k in ("password", "passcode", "2fa", "otp", "token", "secret")):
            return True
        try:
            import re
            if re.search(r"\b\d{6,}\b", text):
                return True
            if re.search(r"[A-Za-z0-9+/=]{20,}", text):
                return True
        except Exception:
            pass
        return False

    def _store_ui_lesson(
        self,
        *,
        objective: str,
        plan_summary: str,
        question: str,
        answer: str,
        ui_state: Dict[str, Any],
    ) -> None:
        """Store a UI correction lesson for future runs."""
        if not answer or self._looks_sensitive(answer):
            return
        try:
            from agent.memory.unified_memory import store_lesson

            analysis = ui_state.get("analysis") if isinstance(ui_state, dict) else None
            observation = ""
            if isinstance(analysis, dict):
                observation = analysis.get("observation", "")
            screenshot = ui_state.get("screenshot") if isinstance(ui_state, dict) else None
            context = (
                f"Objective: {objective}\n"
                f"Plan: {plan_summary}\n"
                f"Observation: {observation}\n"
                f"Question: {question}\n"
                f"User instruction: {answer}\n"
                f"Screenshot: {screenshot}"
            )
            store_lesson(
                lesson=f"UI correction: {answer}",
                context=context,
                tags=["ui_correction", "human_guidance"],
            )
        except Exception as exc:
            logger.debug(f"Could not store UI lesson: {exc}")

    def run(self, user_request: str) -> TaskResult:
        """
        Execute a user request autonomously.

        This is the main entry point with the CORRECT flow.
        """
        self.initialize()

        self._status(f"Processing: {user_request}")

        # ============================================================
        # STEP 1: Parse intent and identify what we need
        # ============================================================
        self._status("Step 1: Parsing intent...")
        intent = self._parse_intent(user_request)

        self._status(f"  -> Action: {intent.action}")
        self._status(f"  -> Service: {intent.service or 'unknown'}")
        self._status(f"  -> Needs auth: {intent.needs_auth}")

        # Ask clarifying questions if needed
        if intent.clarifying_questions:
            for question in intent.clarifying_questions:
                answer = self._ask_user(question)
                intent.parameters["user_answer"] = answer
                # Re-parse with additional context
                if "google" in answer.lower():
                    intent.service = "google_calendar"
                    intent.auth_provider = "google"
                elif "outlook" in answer.lower() or "microsoft" in answer.lower():
                    intent.service = "outlook"
                    intent.auth_provider = "microsoft"

        is_local_task = self._is_local_app_task(intent, user_request)

        # ============================================================
        # STEP 2: Check local credentials and skills
        # ============================================================
        self._status("Step 2: Checking local credentials and skills...")

        # Check credentials
        creds_exist = self._check_credentials(intent.auth_provider)
        if creds_exist:
            self._status(f"  [OK] Found {intent.auth_provider} credentials")
        else:
            self._status(f"  [X] No {intent.auth_provider} credentials found")

        # Check if this is a calendar request that needs setup
        # But DON'T auto-execute yet - let it go through research and planning first
        needs_google_setup = (
            intent.action in {"calendar.list_events", "get_calendar_events"}
            and intent.auth_provider == "google"
            and not creds_exist
        )
        if needs_google_setup:
            self._status("  [INFO] Google Calendar setup needed - will proceed to research and planning first")

        # Check skill library
        matching_skills = self.skill_library.search(user_request, k=3)
        if matching_skills:
            best_skill, similarity = matching_skills[0]
            threshold = self._skill_match_threshold(is_local_task)
            if similarity >= threshold:
                self._status(f"  [OK] Found matching skill: {best_skill.name} (confidence: {similarity:.0%})")
                if not best_skill.requires_auth or creds_exist:
                    return self._execute_skill(best_skill, user_request)
            else:
                self._status(f"  ~ Partial match: {best_skill.name} ({similarity:.0%}, threshold={threshold:.0%})")
        else:
            self._status("  [X] No matching skills found")

        # ============================================================
        # STEP 3: Research if we don't know how to do this
        # ============================================================
        if is_local_task:
            self._status("Step 3: Analyzing local app automation task...")
            self._status("  [REASONING] This is a local application task - will use vision-guided automation")
            research = {
                "success": True,
                "summary": "Local app automation using vision-guided desktop automation",
                "execution_steps": [user_request],
                "reasoning": "Local app tasks require UI automation rather than API calls",
            }
        elif not creds_exist or not matching_skills or matching_skills[0][1] < 0.5:
            self._status("Step 3: Researching and reasoning about this task...")
            self._status("  [REASONING] Need to understand:")
            self._status("    - What service/API is required?")
            self._status("    - What authentication is needed?")
            self._status("    - What are the exact steps to complete this?")
            self._status("    - What could go wrong and how to handle it?")
            
            research = self._do_research(user_request, intent)

            if not research["success"]:
                return TaskResult(
                    success=False,
                    summary=f"Could not find how to do this: {research.get('error')}",
                    error=research.get("error"),
                    research_performed=True,
                )

            self._status(f"  [OK] Research complete!")
            self._status(f"  [SUMMARY] {research.get('summary', 'Unknown')}")
            if research.get("sources"):
                self._status(f"\n  [SOURCES] Found {len(research.get('sources', []))} reference sources:")
                for i, source in enumerate(research.get("sources", [])[:5], 1):
                    source_url = source if isinstance(source, str) else source.get("url", source.get("title", "Unknown"))
                    self._status(f"    {i}. {source_url}")
            if research.get("setup_steps"):
                self._status(f"\n  [SETUP STEPS FOUND] {len(research.get('setup_steps', []))} setup steps identified")
            if research.get("execution_steps"):
                self._status(f"  [EXECUTION STEPS FOUND] {len(research.get('execution_steps', []))} execution steps identified")
            if research.get("caveats"):
                self._status(f"\n  [CAVEATS] {len(research.get('caveats', []))} potential issues:")
                for i, caveat in enumerate(research.get("caveats", [])[:3], 1):
                    self._status(f"    {i}. {caveat}")
        else:
            self._status("Step 3: Using existing knowledge...")
            self._status(f"  [REASONING] Found matching skill with {matching_skills[0][1]:.0%} confidence")
            research = {"success": True, "summary": "Using existing knowledge"}

        # ============================================================
        # STEP 4: Create execution plan
        # ============================================================
        self._status("\n" + "=" * 60)
        self._status("STEP 4: CREATING EXECUTION PLAN")
        self._status("=" * 60)
        self._status("Analyzing research findings and building step-by-step plan...")
        plan = self._build_plan(user_request, intent, research, creds_exist)

        self._status("\n" + "=" * 60)
        self._status("📋 TO-DO LIST (EXECUTION PLAN)")
        self._status("=" * 60)
        if not plan.steps:
            self._status("  ⚠️  WARNING: Plan has no steps!")
        else:
            for i, step in enumerate(plan.steps, 1):
                phase_emoji = "🔧" if step.get('phase') == "SETUP" else "✅" if step.get('phase') == "VERIFY" else "⚙️"
                action_type = step.get('action', 'unknown')
                self._status(f"  {i}. {phase_emoji} [{step.get('phase', 'UNKNOWN')}] {step.get('description', 'No description')}")
                if action_type != 'unknown':
                    self._status(f"      → Action: {action_type}")
        self._status("=" * 60)
        self._status(f"\n📊 PLAN SUMMARY:")
        self._status(f"   • Total steps: {len(plan.steps)}")
        self._status(f"   • Plan type: {plan.plan_type}")
        if plan.research_summary:
            self._status(f"   • Based on research: {plan.research_summary[:150]}...")
        self._status("=" * 60 + "\n")

        if plan.plan_type == "SETUP_GUIDE":
            # For Google Calendar/Tasks setup, just show the user what they need to do
            if intent.auth_provider == "google" and (intent.service in {"google_calendar", "google_tasks"} or "google" in (intent.service or "").lower()):
                self._status("\n" + "=" * 60)
                self._status("📋 GOOGLE CALENDAR SETUP REQUIRED")
                self._status("=" * 60)
                self._status("""
To use Google Calendar, you need to:

1. Go to: https://console.cloud.google.com/
2. Create a new project called "treys-agent"
3. Enable the Google Calendar API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download credentials.json to: C:\\Users\\treyt\\.drcodept_swarm\\google_calendar\\credentials.json
6. Come back and ask me again

Once you've completed these steps, I can access your calendar!
""")
                self._status("=" * 60 + "\n")
                return TaskResult(
                    success=False,
                    summary="Google Calendar setup required. Please follow the steps above and try again.",
                    error="Setup needed - follow the instructions provided",
                )
            
            # For other SETUP_GUIDE cases, return the guide
            return TaskResult(
                success=False,
                summary="Setup required. Follow the steps above and re-run your request.",
                steps_taken=0,
            )

        # ============================================================
        # STEP 5: Execute the plan (autonomous - no approval needed)
        # ============================================================
        self._status("  [AUTONOMOUS MODE] Executing plan automatically...")
        plan.approved = True
        self._status("Step 5: Executing plan...")
        result = self._execute_plan(plan)

        # ============================================================
        # STEP 6: Save and learn from execution
        # ============================================================
        if result.success:
            self._status("Step 6: Saving successful procedure as skill...")
            skill_id = self._save_learned_skill(user_request, intent, plan, result)
            result.skill_learned = skill_id
            saved_skill = self.skill_library.get(skill_id) if self.skill_library else None
            if saved_skill:
                self._status(f"  [OK] Saved skill: {saved_skill.name} ({skill_id})")
            else:
                self._status(f"  [OK] Saved skill: {skill_id}")
        else:
            self._status("Step 6: Logging failure for learning...")
            self._log_failure(user_request, intent, plan, result)
            self._status("  [OK] Failure logged to reflexion")

        return result

    def _get_llm(self):
        """Get or create an LLM client for reasoning."""
        if self.llm:
            provider = getattr(self.llm, 'provider', 'unknown')
            if 'codex' in provider.lower():
                return self.llm
        
        try:
            from agent.llm.codex_cli_client import CodexCliClient
            client = CodexCliClient.from_env()
            # Don't check auth - let Codex try and fail naturally at runtime if needed
            self.llm = client
            self._status("[LLM] provider=codex_cli model=default (USING CODEX)")
            return self.llm
        except Exception as e:
            logger.warning(f"Codex CLI error: {e}")
        
        # Only fall back to OpenRouter if Codex completely unavailable
        if os.getenv("OPENROUTER_API_KEY"):
            try:
                from agent.llm.openrouter_client import OpenRouterClient        
                self.llm = OpenRouterClient.from_env()
                self._status(f"[LLM] provider=openrouter model={self.llm.model} (FALLBACK)")
                return self.llm
            except Exception as e:
                logger.warning(f"OpenRouter not available: {e}")
        
        return None

    def _skill_match_threshold(self, is_local_task: bool) -> float:
        """Determine skill reuse threshold."""
        default_raw = os.getenv("SKILL_MATCH_THRESHOLD", "0.7").strip()
        local_raw = os.getenv("SKILL_MATCH_THRESHOLD_LOCAL", "").strip()
        try:
            default_val = float(default_raw)
        except Exception:
            default_val = 0.7
        if is_local_task:
            if local_raw:
                try:
                    return float(local_raw)
                except Exception:
                    return max(0.6, default_val)
            return max(0.6, default_val)
        return default_val

    def _should_use_notepad_file(self, skill, original_request: str) -> bool:
        """Prefer deterministic Notepad flow when configured."""
        mode = os.getenv("AGENT_NOTEPAD_MODE", "file").strip().lower()
        if mode != "file":
            return False
        text = (original_request or "").lower()
        tags = {t.lower() for t in (getattr(skill, "tags", []) or [])}
        if "notepad" not in text and "notepad" not in tags:
            return False
        keywords = ("write", "type", "message", "note", "draft")
        return any(k in text for k in keywords)

    def _extract_message_from_request(self, text: str) -> Optional[str]:
        """Extract a message to write from the user request."""
        if not text:
            return None
        lowered = text.lower()
        if "make it up" in lowered:
            return None
        # Quoted content
        try:
            import re
            match = re.search(r"['\"]([^'\"]{3,})['\"]", text)
            if match:
                return match.group(1).strip()
        except Exception:
            pass
        # Simple heuristic: text after "write"
        if "write" in lowered:
            parts = text.split("write", 1)
            if len(parts) == 2:
                candidate = parts[1].strip(" .:")
                if candidate and len(candidate) > 3:
                    return candidate
        return None

    def _generate_motivational_message(self) -> str:
        """Generate a short motivational message."""
        llm = self._get_llm()
        prompt = (
            "Write a short motivational message (1-2 sentences). "
            "No quotes, no emojis."
        )
        try:
            if hasattr(llm, "generate_text"):
                return llm.generate_text(prompt, system="Return only the message.")  # type: ignore[arg-type]
            if hasattr(llm, "chat"):
                try:
                    return llm.chat(prompt, timeout_seconds=20)  # type: ignore[arg-type]
                except TypeError:
                    return llm.chat(prompt)  # type: ignore[arg-type]
        except Exception:
            pass
        return "Keep going. Your effort today is building the strength you need tomorrow."

    def _notepad_output_path(self) -> Path:
        """Get the output path for Notepad file-based automation."""
        env_file = os.getenv("AGENT_NOTEPAD_FILE", "").strip()
        if env_file:
            return Path(env_file)
        env_dir = os.getenv("AGENT_NOTEPAD_DIR", "").strip()
        base_dir = Path(env_dir) if env_dir else (Path.home() / ".drcodept" / "notes")
        return base_dir / "notepad_message.txt"

    def _should_verify_ui(self) -> bool:
        return os.getenv("AGENT_VERIFY_UI", "1").strip().lower() in {"1", "true", "yes", "y", "on"}

    def _verify_strict(self) -> bool:
        return os.getenv("AGENT_VERIFY_STRICT", "0").strip().lower() in {"1", "true", "yes", "y", "on"}

    def _screenshot_dir(self) -> Path:
        base = os.getenv("AGENT_SCREENSHOT_DIR", "").strip()
        if base:
            return Path(base)
        return Path.home() / ".drcodept" / "screenshots"

    def _take_screenshot(self, prefix: str = "notepad") -> Optional[Path]:
        try:
            import pyautogui
        except Exception:
            return None
        try:
            out_dir = self._screenshot_dir()
            out_dir.mkdir(parents=True, exist_ok=True)
            path = out_dir / f"{prefix}_{int(time.time())}.png"
            pyautogui.screenshot(str(path))
            return path
        except Exception:
            return None

    def _ocr_text(self, image_path: Path) -> str:
        try:
            from PIL import Image
            import pytesseract
        except Exception:
            return ""
        try:
            img = Image.open(image_path)
            return pytesseract.image_to_string(img) or ""
        except Exception:
            return ""

    def _verify_message_in_screenshot(self, image_path: Optional[Path], message: str) -> Tuple[bool, str]:
        if not image_path or not image_path.exists():
            return False, "No screenshot available for verification"
        ocr_text = self._ocr_text(image_path)
        if not ocr_text.strip():
            return False, "OCR unavailable or empty"
        # Normalize and compare word coverage
        def _words(text: str) -> List[str]:
            import re
            return [w for w in re.findall(r"[a-zA-Z0-9']+", text.lower()) if len(w) > 2]
        msg_words = _words(message)
        if not msg_words:
            return False, "No message words to verify"
        ocr_words = set(_words(ocr_text))
        hits = sum(1 for w in msg_words if w in ocr_words)
        ratio = hits / max(1, len(msg_words))
        if ratio >= 0.6:
            return True, f"OCR match {ratio:.0%}"
        return False, f"OCR match too low ({ratio:.0%})"

    def _verify_message_in_text(self, text: str, message: str) -> Tuple[bool, str]:
        if not text.strip():
            return False, "UI text empty"
        def _words(val: str) -> List[str]:
            import re
            return [w for w in re.findall(r"[a-zA-Z0-9']+", val.lower()) if len(w) > 2]
        msg_words = _words(message)
        if not msg_words:
            return False, "No message words to verify"
        text_words = set(_words(text))
        hits = sum(1 for w in msg_words if w in text_words)
        ratio = hits / max(1, len(msg_words))
        if ratio >= 0.7:
            return True, f"UI text match {ratio:.0%}"
        return False, f"UI text match too low ({ratio:.0%})"

    def _read_notepad_text(self) -> Tuple[Optional[str], str]:
        """Try to read Notepad text via UI automation libraries."""
        # Try uiautomation
        try:
            import uiautomation as auto
            win = auto.WindowControl(searchDepth=1, SubName="Notepad")
            if win.Exists(maxSearchSeconds=1):
                for ctrl in (win.DocumentControl, win.EditControl):
                    try:
                        doc = ctrl(searchDepth=6)
                        if doc.Exists(maxSearchSeconds=1):
                            try:
                                pattern = doc.GetTextPattern()
                                if pattern:
                                    return pattern.DocumentRange.GetText(-1), "uiautomation_textpattern"
                            except Exception:
                                pass
                            try:
                                vp = doc.GetValuePattern()
                                return vp.Value, "uiautomation_valuepattern"
                            except Exception:
                                pass
                            try:
                                return doc.Name, "uiautomation_name"
                            except Exception:
                                pass
                    except Exception:
                        pass
        except Exception:
            pass

        # Try pywinauto
        try:
            from pywinauto import Desktop
            win = Desktop(backend="uia").window(title_re=".*Notepad.*")
            if win.exists(timeout=1):
                try:
                    edit = win.child_window(control_type="Edit")
                    if edit.exists(timeout=1):
                        try:
                            return edit.get_value(), "pywinauto_get_value"
                        except Exception:
                            pass
                        try:
                            return edit.window_text(), "pywinauto_window_text"
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            pass

        return None, "ui_text_unavailable"

    def _is_process_running(self, process_name: str) -> bool:
        try:
            result = subprocess.run(
                ["tasklist", "/FI", f"IMAGENAME eq {process_name}"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            return process_name.lower() in (result.stdout or "").lower()
        except Exception:
            return False

    def _get_notepad_window_titles(self) -> List[str]:
        try:
            cmd = (
                "Get-Process -Name notepad -ErrorAction SilentlyContinue | "
                "ForEach-Object { $_.MainWindowTitle }"
            )
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", cmd],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode != 0:
                return []
            return [line.strip() for line in (result.stdout or "").splitlines() if line.strip()]
        except Exception:
            return []

    def _execute_notepad_file(self, original_request: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Write text to a file and open it in Notepad, then verify via screenshot."""
        message = self._extract_message_from_request(original_request)
        if not message:
            message = self._generate_motivational_message()
        if not message:
            return False, "No message to write", {}

        path = self._notepad_output_path()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(message.strip() + "\n", encoding="utf-8")
        except Exception as exc:
            return False, f"Failed to write message file: {exc}", {}

        def _launch() -> Optional[Exception]:
            try:
                subprocess.Popen(["notepad.exe", str(path)])
                return None
            except Exception as exc:
                return exc

        err = _launch()
        if err:
            return False, f"Failed to launch Notepad: {err}", {}

        evidence: Dict[str, Any] = {"file_path": str(path), "message": message}
        file_ok = False
        file_reason = "file_verification_unavailable"
        try:
            file_text = path.read_text(encoding="utf-8")
            file_ok, file_reason = self._verify_message_in_text(file_text, message)
        except Exception as exc:
            file_reason = f"file_read_failed: {exc}"
        evidence["file_verification"] = file_reason
        if not self._should_verify_ui():
            return True, f"Wrote message to {path} and opened Notepad", evidence

        # Verification with UI text read or screenshot + OCR (retry once if low match)
        time.sleep(1.2)
        notepad_running = self._is_process_running("notepad.exe")
        evidence["notepad_running"] = notepad_running
        titles = self._get_notepad_window_titles()
        if titles:
            evidence["notepad_titles"] = titles
            evidence["notepad_title_match"] = any(path.name.lower() in t.lower() for t in titles)

        shot = self._take_screenshot("notepad")
        if shot:
            evidence["screenshot"] = str(shot)

        ok = False
        reason = "unverified"
        ui_text, ui_method = self._read_notepad_text()
        if ui_text:
            ok, reason = self._verify_message_in_text(ui_text, message)
            evidence.update({"ui_read_method": ui_method, "verification": reason, "verification_level": "ui_text"})
        else:
            if not shot:
                shot = self._take_screenshot("notepad")
                if shot:
                    evidence["screenshot"] = str(shot)
            ok, reason = self._verify_message_in_screenshot(shot, message)
            evidence.update({"verification": reason})
            if ok:
                evidence["verification_level"] = "ocr"
        if not ok:
            time.sleep(1.0)
            _launch()
            time.sleep(1.2)
            notepad_running_retry = self._is_process_running("notepad.exe")
            evidence["notepad_running_retry"] = notepad_running_retry
            titles_retry = self._get_notepad_window_titles()
            if titles_retry:
                evidence["notepad_titles_retry"] = titles_retry
                evidence["notepad_title_match_retry"] = any(path.name.lower() in t.lower() for t in titles_retry)
            ui_text2, ui_method2 = self._read_notepad_text()
            if ui_text2:
                ok2, reason2 = self._verify_message_in_text(ui_text2, message)
                evidence.update({
                    "ui_read_method_retry": ui_method2,
                    "verification_retry": reason2,
                    "verification_level_retry": "ui_text",
                })
                ok = ok2
                reason = reason2
            else:
                shot2 = self._take_screenshot("notepad_retry")
                ok2, reason2 = self._verify_message_in_screenshot(shot2, message)
                evidence.update({
                    "screenshot_retry": str(shot2) if shot2 else None,
                    "verification_retry": reason2,
                    "verification_level_retry": "ocr",
                })
                ok = ok2
                reason = reason2

        if not ok:
            # Fall back to file + process evidence if strong verification is unavailable
            title_match = bool(evidence.get("notepad_title_match") or evidence.get("notepad_title_match_retry"))
            notepad_running_final = bool(evidence.get("notepad_running_retry", evidence.get("notepad_running")))
            if file_ok and (notepad_running_final or title_match):
                evidence["verification_warning"] = reason
                evidence["verification_level"] = "file+process" if notepad_running_final else "file+title"
                if self._verify_strict():
                    return False, f"Verification failed: {reason}", evidence
                return True, f"Wrote message to {path} (verification warning: {reason})", evidence
            if file_ok:
                evidence["verification_warning"] = reason
                evidence["verification_level"] = "file_only"
                if self._verify_strict():
                    return False, f"Verification failed: {reason}", evidence
                return True, f"Wrote message to {path} (verification warning: {reason})", evidence
            return False, f"Verification failed: {reason}", evidence

        return True, f"Wrote message to {path} and opened Notepad", evidence

    def _log_llm_use(self, llm, purpose: str) -> None:
        provider = getattr(llm, "provider", getattr(llm, "provider_name", "unknown"))
        model = getattr(llm, "model", "unknown")
        self._status(f"[LLM] purpose={purpose} provider={provider} model={model}")

    def _try_codex_auto_login(self) -> bool:
        """
        Attempt automatic Codex login using the hybrid executor.

        The agent figures out how to login by looking at the screen,
        NOT by following a rigid script.
        """
        try:
            from agent.tools.credential_store import get_credential_store

            store = get_credential_store()
            if not store.has_credentials("openai"):
                self._status("No OpenAI credentials stored. Skipping auto-login.")
                return False

            creds = store.get("openai")
            if not creds:
                return False

            self._status("Attempting Codex auto-login...")

            # Start codex login (opens browser)
            import subprocess
            import shutil
            codex_bin = shutil.which("codex") or r"C:\Users\treyt\AppData\Roaming\npm\node_modules\@openai\codex\vendor\x86_64-pc-windows-msvc\codex\codex.exe"

            if not os.path.exists(codex_bin):
                self._status("  Codex CLI not found")
                return False

            subprocess.Popen([codex_bin, "login"])
            time.sleep(3)  # Wait for browser

            # Let the hybrid executor handle the login
            # It will look at the screen and figure out what to do
            result = self.executor.run_task(
                objective=f"Log into OpenAI with email '{creds.get('email')}' and password",
                context=f"""You are on the OpenAI login page.
                Email: {creds.get('email')}
                Password: {creds.get('password')}

                Look at the screen, find the input fields, and complete the login.
                If there's a verification code needed, ask the user for it.""",
                on_step=lambda s: self._status(f"    {s.get('action', {}).get('reasoning', '')[:60]}"),
                on_user_input=self._ask_user,
            )

            if result.get("success"):
                self._status("  [OK] Codex auto-login successful!")
                return True
            else:
                self._status(f"  [X] Auto-login failed: {result.get('summary')}")
                return False

        except Exception as e:
            logger.warning(f"Auto-login failed: {e}")
            return False

    def _call_llm_json(
        self,
        prompt: str,
        schema: Dict[str, Any],
        timeout: int = 60,
        model_cls: Optional[type] = None,
    ) -> Optional[Dict[str, Any]]:
        """Call LLM and get structured JSON output with schema enforcement."""
        llm = self._get_llm()
        if not llm:
            return None

        schema_path = Path(tempfile.gettempdir()) / f"schema_{uuid4().hex[:8]}.json"
        schema_path.write_text(json.dumps(schema), encoding="utf-8")

        def _call(current_llm, message: str) -> Optional[Dict[str, Any]]:
            if hasattr(current_llm, "reason_json"):
                return current_llm.reason_json(
                    message,
                    schema_path=schema_path,
                    timeout_seconds=timeout,
                )
            if hasattr(current_llm, "complete_json"):
                return current_llm.complete_json(
                    message,
                    schema_path=schema_path,
                    timeout_seconds=timeout,
                )
            return None

        active_llm = llm

        def _retry_call(repair_prompt: str) -> Optional[str]:
            try:
                self._log_llm_use(active_llm, "json_repair")
                repaired = _call(active_llm, repair_prompt)
                if repaired is None:
                    return None
                return json.dumps(repaired)
            except Exception:
                return None

        try:
            self._log_llm_use(llm, "json")
            raw = _call(llm, prompt)
        except Exception as e:
            error_str = str(e).lower()
            # Only disable Codex on clear authentication/availability issues, not any error containing "codex"
            should_disable = ("not authenticated" in error_str or 
                            ("auth" in error_str and ("fail" in error_str or "error" in error_str)) or
                            "not found" in error_str)
            if should_disable:
                self._disable_codex = True
                try:
                    from agent.llm.openrouter_client import OpenRouterClient
                    fallback_llm = OpenRouterClient.from_env()
                    self._log_llm_use(fallback_llm, "json_fallback")
                    raw = _call(fallback_llm, prompt)
                    if raw is not None:
                        active_llm = fallback_llm
                except Exception as fallback_e:
                    logger.error(f"OpenRouter fallback also failed: {fallback_e}")
                    raw = None
            else:
                # Don't disable Codex on temporary errors - just log and fail this call
                logger.warning(f"LLM call failed (non-fatal): {e}")
                raw = None

        if raw is None:
            try:
                schema_path.unlink()
            except Exception:
                pass
            return None

        if not model_cls:
            try:
                schema_path.unlink()
            except Exception:
                pass
            return raw if isinstance(raw, dict) else None

        raw_text = json.dumps(raw) if isinstance(raw, dict) else str(raw)
        validated, error = enforce_json_response(
            raw_text,
            model_cls=model_cls,
            schema=schema,
            retry_call=_retry_call,
            max_retries=2,
        )
        if validated is not None:
            try:
                schema_path.unlink()
            except Exception:
                pass
            return validated

        logger.warning(f"LLM JSON validation failed after repair: {error}")
        try:
            schema_path.unlink()
        except Exception:
            pass
        return {"error": "invalid_json", "details": error}

    def _call_llm_chat(self, prompt: str, timeout: int = 60) -> Optional[str]:
        """Call LLM for free-form chat."""
        llm = self._get_llm()
        if not llm:
            return None

        try:
            # OpenRouter uses different signature
            if hasattr(llm, 'chat'):
                self._log_llm_use(llm, "chat")
                try:
                    return llm.chat(prompt, timeout_seconds=timeout)
                except TypeError:
                    # OpenRouter doesn't take timeout_seconds
                    return llm.chat(prompt)
            return None
        except Exception as e:
            # Only disable Codex on clear authentication/availability issues
            error_str = str(e).lower()
            should_disable = ("not authenticated" in error_str or 
                            ("auth" in error_str and ("fail" in error_str or "error" in error_str)) or
                            "not found" in error_str)
            if should_disable:
                self._disable_codex = True
                try:
                    from agent.llm.openrouter_client import OpenRouterClient
                    fallback_llm = OpenRouterClient.from_env()
                    self._log_llm_use(fallback_llm, "chat_fallback")
                    return fallback_llm.chat(prompt)
                except Exception:
                    pass
            # Don't disable Codex on temporary errors - just log and fail this call
            logger.warning(f"LLM chat failed (non-fatal): {e}")
            return None

    def _parse_intent(self, request: str) -> ParsedIntent:
        """
        Parse the user's intent using the LLM.

        The LLM understands what the user wants and structures it.
        Falls back to pattern matching if LLM is unavailable.
        """
        # Try LLM-based parsing first
        llm_result = self._parse_intent_with_llm(request)
        if llm_result:
            return llm_result

        # Fallback to pattern matching
        self._status("  (Using pattern matching fallback)")
        return self._parse_intent_fallback(request)

    def _parse_intent_with_llm(self, request: str) -> Optional[ParsedIntent]:
        """Use LLM to understand the user's intent."""
        prompt = f"""You are an intent parser. Analyze this user request and extract the structured intent.

USER REQUEST: "{request}"

Determine:
1. What action they want (e.g., calendar.list_events, send_email, create_event, search_web, open_app)
2. What service is needed (e.g., google_calendar, outlook, gmail, notion, slack)
3. What authentication provider is needed (google, microsoft, or null if none)
4. Whether authentication is required
5. Extract any parameters (time ranges, dates, recipients, subjects)
6. If anything is ambiguous, list clarifying questions to ask

Be specific about the service. If they mention "calendar" without specifying which one, ask which service they use.
If they mention "tomorrow" or "today", extract that as a time_range parameter.

Return a JSON object matching the schema."""

        result = self._call_llm_json(prompt, INTENT_SCHEMA, timeout=30, model_cls=IntentPayload)

        if not result:
            return None

        # Check for errors
        if "error" in result:
            logger.warning(f"LLM intent parsing error: {result.get('error')}")
            return None

        try:
            action = self._normalize_intent_action(
                result.get("action", "unknown"),
                result.get("service"),
            )
            return ParsedIntent(
                action=action,
                service=result.get("service"),
                parameters=result.get("parameters", {}),
                needs_auth=result.get("needs_auth", False),
                auth_provider=result.get("auth_provider"),
                clarifying_questions=result.get("clarifying_questions", []),
            )
        except Exception as e:
            logger.warning(f"Could not create ParsedIntent from LLM result: {e}")
            return None

    def _normalize_intent_action(self, action: str, service: Optional[str]) -> str:
        """Normalize intent action names for internal routing."""
        action_clean = (action or "").strip()
        if action_clean in {"get_calendar_events", "list_calendar_events", "calendar_list_events"}:
            return "calendar.list_events"
        if service and "calendar" in service and action_clean == "list_events":
            return "calendar.list_events"
        return action_clean or "unknown"

    def _is_local_app_task(self, intent: ParsedIntent, request: str) -> bool:
        """Check if the request targets a local desktop app."""
        local_apps = {
            "notepad",
            "calculator",
            "paint",
            "wordpad",
            "file explorer",
            "explorer",
            "cmd",
            "powershell",
        }
        service = (intent.service or "").lower().strip()
        if service in local_apps:
            return True
        request_lower = request.lower()
        return any(app in request_lower for app in local_apps)

    def _parse_intent_fallback(self, request: str) -> ParsedIntent:
        """Fallback pattern-based intent parsing."""
        request_lower = request.lower()

        # Detect service
        service = None
        auth_provider = None
        needs_auth = False

        if "google" in request_lower or "gmail" in request_lower:
            auth_provider = "google"
            needs_auth = True
            if "calendar" in request_lower:
                service = "google_calendar"
            elif "email" in request_lower or "gmail" in request_lower:
                service = "gmail"
        elif "outlook" in request_lower or "microsoft" in request_lower:
            auth_provider = "microsoft"
            needs_auth = True
            if "calendar" in request_lower:
                service = "outlook_calendar"
            elif "email" in request_lower:
                service = "outlook_email"
        elif "calendar" in request_lower:
            needs_auth = True

        # Detect action
        action = "unknown"
        if "calendar" in request_lower:
            if any(w in request_lower for w in ["what", "show", "list", "get", "tell"]):
                action = "calendar.list_events"
            elif any(w in request_lower for w in ["add", "create", "schedule"]):
                action = "create_calendar_event"
        elif "email" in request_lower:
            if any(w in request_lower for w in ["send", "compose", "write"]):
                action = "send_email"
            elif any(w in request_lower for w in ["read", "check", "show"]):
                action = "get_emails"

        # Detect time parameters
        parameters = {}
        if "tomorrow" in request_lower:
            parameters["time_range"] = "tomorrow"
        elif "today" in request_lower:
            parameters["time_range"] = "today"
        elif "this week" in request_lower:
            parameters["time_range"] = "this_week"

        # Clarifying questions
        questions = []
        if needs_auth and not auth_provider:
            questions.append("Which calendar service do you use - Google Calendar or Microsoft Outlook?")

        return ParsedIntent(
            action=self._normalize_intent_action(action, service),
            service=service,
            parameters=parameters,
            needs_auth=needs_auth,
            auth_provider=auth_provider,
            clarifying_questions=questions,
        )

    def _check_credentials(self, provider: Optional[str]) -> bool:
        """Check if we have credentials for a provider."""
        if not provider:
            return False

        if provider == "google":
            try:
                from agent.skills.google_calendar import GoogleCalendarSkill
                from agent.skills.base import AuthStatus
            except Exception:
                return False

            skill = GoogleCalendarSkill()
            status = skill.auth_status()
            return status in {AuthStatus.AUTHENTICATED, AuthStatus.AUTH_EXPIRED}
        elif provider == "microsoft":
            # TODO: Check Microsoft credentials
            return False
        return False

    def _handle_calendar_request(self, intent: ParsedIntent) -> Optional[TaskResult]:
        """Handle Google Calendar list requests directly via the skill."""
        if intent.action not in {"calendar.list_events", "get_calendar_events"}:
            return None
        if intent.auth_provider != "google":
            return None

        try:
            from agent.skills.google_calendar import GoogleCalendarSkill
            from agent.skills.base import AuthStatus
        except Exception as exc:
            return TaskResult(
                success=False,
                summary=f"Google Calendar skill unavailable: {exc}",
                error=str(exc),
            )

        skill = GoogleCalendarSkill()
        status = skill.auth_status()
        if status == AuthStatus.NOT_CONFIGURED:
            # Just tell user what to do
            self._status("  [INFO] Google Calendar not configured")
            self._status("""
To use Google Calendar, you need to:

1. Go to: https://console.cloud.google.com/
2. Create a new project called "treys-agent"  
3. Enable the Google Calendar API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download credentials.json to: C:\\Users\\treyt\\.drcodept_swarm\\google_calendar\\credentials.json
6. Come back and ask me again

Once you've completed these steps, I can access your calendar!
""")
            return TaskResult(
                success=False,
                summary="Google Calendar setup required. Please follow the steps above and try again.",
                error="Setup needed",
            )

        time_range = intent.parameters.get("time_range", "tomorrow")
        now = datetime.now().astimezone()
        if time_range == "tomorrow":
            result = skill.list_tomorrow_events()
        else:
            if time_range == "today":
                start = datetime.combine(now.date(), datetime.min.time(), tzinfo=now.tzinfo)
                end = start + timedelta(days=1)
            elif time_range == "this_week":
                start = datetime.combine(now.date(), datetime.min.time(), tzinfo=now.tzinfo)
                end = start + timedelta(days=7)
            else:
                start = datetime.combine(now.date(), datetime.min.time(), tzinfo=now.tzinfo)
                end = start + timedelta(days=1)
            result = skill.list_events(time_min=start, time_max=end)

        if result.ok:
            events = result.data or []
            if events:
                lines = []
                for evt in events:
                    start = evt.get("start", {})
                    when = start.get("dateTime") or start.get("date") or "unknown time"
                    lines.append(f"- {evt.get('summary', 'Untitled')} at {when}")
                summary = f"Found {len(events)} events:\n" + "\n".join(lines[:10])
            else:
                summary = f"No events found for {time_range}"
            return TaskResult(
                success=True,
                summary=summary,
                steps_taken=1,
                evidence={"events": events},
            )

        if result.needs_auth:
            guide = skill.setup_guide()
            return TaskResult(
                success=False,
                summary=guide,
                error=result.error or "Calendar authentication required",
            )

        return TaskResult(
            success=False,
            summary=result.error or "Failed to list calendar events",
            error=result.error,
        )

    def _generate_search_query(self, request: str, intent: ParsedIntent) -> str:
        """Use LLM to generate an optimal search query."""
        # Try LLM first
        llm_query = self._call_llm_chat(
            f"""Generate a concise web search query to find how to accomplish this task:

Task: {request}
Service: {intent.service or 'unknown'}
Auth provider: {intent.auth_provider or 'unknown'}
Action: {intent.action}

Generate a search query that would find:
- Setup instructions
- API documentation
- OAuth/authentication steps
- Python code examples

Return ONLY the search query, nothing else. Keep it under 10 words.""",
            timeout=15
        )

        if llm_query and len(llm_query.strip()) > 5:
            return llm_query.strip().strip('"').strip("'")

        # Fallback to pattern-based query
        service = intent.service or "API"
        auth = intent.auth_provider or ""

        if intent.action in {"get_calendar_events", "calendar.list_events"}:
            return f"{auth} calendar API Python setup tutorial OAuth"
        elif intent.action == "create_calendar_event":
            return f"{auth} calendar API create event Python"
        elif intent.action == "send_email":
            return f"{auth} email API Python send tutorial"
        else:
            return f"{auth} {service} API Python setup OAuth tutorial"

    def _do_research(self, request: str, intent: ParsedIntent) -> Dict[str, Any]:
        """
        Research how to accomplish the request using PROPER web search.

        Uses the LLM to generate smart search queries and summarize findings.
        Falls back to pattern-based queries if LLM is unavailable.
        """
        try:
            from agent.autonomous.config import RunContext
            from agent.autonomous.tools.builtins import WebSearchArgs, WebFetchArgs, web_search, web_fetch

            # Use LLM to generate a better search query
            query = self._generate_search_query(request, intent)

            self._status(f"\n  🔍 RESEARCH: Generating search query...")
            self._status(f"  📝 Query: {query}")
            self._status(f"  ⏳ Searching web for relevant information...")

            # Create context for the tools
            ctx = RunContext(
                run_id="research",
                run_dir=REPO_ROOT / "runs" / "research",
                workspace_dir=REPO_ROOT,
                profile=None,
                usage=None,
            )

            # Search the web
            search_result = web_search(ctx, WebSearchArgs(query=query, max_results=5))

            if not search_result.success:
                self._status(f"  ❌ Search failed: {search_result.error}")
                self._status(f"  ⚠️  Falling back to pattern-based research...")
                return self._fallback_research(intent)
            
            results = search_result.output.get("results", [])
            self._status(f"  ✅ Search successful! Found {len(results)} results")
            if not results:
                hint = self._ask_user(
                    "Research returned no results. Provide a URL or keyword to search (or press Enter to use built-in steps)."
                )
                if hint:
                    if hint.strip().lower().startswith(("http://", "https://")):
                        results = [{"url": hint.strip(), "title": hint.strip(), "snippet": ""}]
                    else:
                        search_result = web_search(ctx, WebSearchArgs(query=hint.strip(), max_results=5))
                        results = search_result.output.get("results", []) if search_result.success else []
                if not results:
                    return self._fallback_research(intent)

            # Prefer authoritative sources first
            preferred_domains = [
                "developers.google.com",
                "cloud.google.com",
                "support.google.com",
                "learn.microsoft.com",
                "docs.microsoft.com",
            ]

            def _score_result(item: Dict[str, Any]) -> int:
                url = (item or {}).get("url") or ""
                host = urlparse(url).netloc.lower()
                return 1 if any(host.endswith(d) for d in preferred_domains) else 0

            results = sorted(results, key=_score_result, reverse=True)

            max_sources = int(os.getenv("TREYS_AGENT_RESEARCH_MAX_SOURCES", "3"))
            excerpt_chars = int(os.getenv("TREYS_AGENT_RESEARCH_EXCERPT_CHARS", "4000"))

            sources = []
            excerpts = []
            for result in results[:max_sources]:
                url = result.get("url", "")
                title = result.get("title", "")
                snippet = result.get("snippet", "") or ""
                if not url:
                    continue
                fetch = web_fetch(ctx, WebFetchArgs(url=url, strip_html=True, timeout_seconds=20))
                text = ""
                if fetch.success and isinstance(fetch.output, dict):
                    text = (fetch.output.get("text") or "").strip()
                excerpt = (text or snippet)[:excerpt_chars]
                if excerpt:
                    excerpts.append(f"Source: {title}\nURL: {url}\nEXCERPT:\n{excerpt}")
                    sources.append(url)

            if excerpts:
                prompt = (
                    "You are a research assistant. Use ONLY the sources below to produce a concrete plan.\n"
                    "Return JSON with summary, setup_steps, execution_steps, success_checks, caveats, sources.\n"
                    f"Objective: {request}\n"
                    f"Service: {intent.service}\n"
                    f"Auth Provider: {intent.auth_provider}\n\n"
                    "SOURCES:\n"
                    + "\n\n".join(excerpts)
                )
                payload = self._call_llm_json(prompt, RESEARCH_SCHEMA, timeout=45, model_cls=ResearchPayload)
                if payload and "summary" in payload:
                    return {
                        "success": True,
                        "summary": payload.get("summary", ""),
                        "service": intent.service,
                        "auth_provider": intent.auth_provider,
                        "setup_steps": payload.get("setup_steps") or self._get_setup_steps(intent),
                        "execution_steps": payload.get("execution_steps") or self._get_execution_steps(intent),
                        "success_checks": payload.get("success_checks") or [],
                        "caveats": payload.get("caveats") or [],
                        "sources": payload.get("sources") or sources,
                    }

            # Fallback: use snippets-only summary if fetch or synthesis failed
            summaries = []
            for result in results[:3]:
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                summaries.append(f"- {title}: {snippet[:200]}")

            summary = self._build_research_summary(intent, summaries)

            return {
                "success": True,
                "summary": summary,
                "service": intent.service,
                "auth_provider": intent.auth_provider,
                "setup_steps": self._get_setup_steps(intent),
                "execution_steps": self._get_execution_steps(intent),
                "sources": sources,
            }

        except Exception as e:
            logger.error(f"Research failed: {e}")
            return self._fallback_research(intent)

    def _fallback_research(self, intent: ParsedIntent) -> Dict[str, Any]:
        """Fallback research using built-in knowledge."""
        if intent.auth_provider == "google":
            return {
                "success": True,
                "summary": "Set up Google Calendar API with OAuth",
                "service": "google_calendar",
                "auth_provider": "google",
                "documentation_url": "https://console.cloud.google.com/",
                "setup_steps": [
                    "Go to Google Cloud Console",
                    "Create a new project (or select existing)",
                    "Enable Google Calendar API",
                    "Configure OAuth consent screen",
                    "Create OAuth credentials",
                    "Download credentials.json",
                    "Complete OAuth flow",
                ],
                "execution_steps": [
                    "Use credentials to call Calendar API",
                    "List events for the requested time period",
                ],
            }
        elif intent.auth_provider == "microsoft":
            return {
                "success": True,
                "summary": "Set up Microsoft Graph API with OAuth",
                "service": "outlook",
                "auth_provider": "microsoft",
                "documentation_url": "https://portal.azure.com/",
                "setup_steps": [
                    "Go to Azure Portal",
                    "Register an application",
                    "Configure API permissions for Calendar",
                    "Create client secret",
                    "Complete OAuth flow",
                ],
                "execution_steps": [
                    "Use tokens to call Graph API",
                    "List calendar events",
                ],
            }
        else:
            return {
                "success": False,
                "error": "Unknown service - need more information",
            }

    def _build_research_summary(self, intent: ParsedIntent, web_summaries: List[str]) -> str:
        """Build a summary from research results using LLM."""
        # Try LLM-based summarization
        web_content = "\n".join(web_summaries)

        llm_summary = self._call_llm_chat(
            f"""Summarize these web search results into a concise action plan.

ACTION NEEDED: {intent.action}
SERVICE: {intent.service}
AUTH PROVIDER: {intent.auth_provider}

WEB RESULTS:
{web_content}

Create a brief summary (2-3 sentences) explaining:
1. What steps are needed
2. What authentication/setup is required
3. Key things to watch out for

Be specific and actionable.""",
            timeout=20
        )

        if llm_summary and len(llm_summary.strip()) > 20:
            return llm_summary.strip()

        # Fallback
        if intent.auth_provider == "google":
            return f"To access Google Calendar: 1) Set up Google Cloud project, 2) Enable Calendar API, 3) Create OAuth credentials, 4) Complete OAuth flow. Web results: {'; '.join(web_summaries[:2])}"
        elif intent.auth_provider == "microsoft":
            return f"To access Outlook Calendar: 1) Register app in Azure, 2) Configure Calendar permissions, 3) Complete OAuth flow. Web results: {'; '.join(web_summaries[:2])}"
        return f"Research results: {'; '.join(web_summaries)}"

    def _get_setup_steps(self, intent: ParsedIntent) -> List[str]:
        """Get setup steps based on intent."""
        if intent.auth_provider == "google":
            creds_path = Path.home() / ".drcodept_swarm" / "google_calendar" / "credentials.json"
            return [
                "Open Google Cloud Console in browser",
                "Create or select a project",
                "Enable Google Calendar API",
                "Configure OAuth consent screen",
                "Create OAuth 2.0 credentials",
                f"Download credentials.json and save to: {creds_path}",
                "Run OAuth flow to get token",
            ]
        elif intent.auth_provider == "microsoft":
            return [
                "Open Azure Portal in browser",
                "Go to App Registrations",
                "Create new registration",
                "Add Calendar API permissions",
                "Create client secret",
                "Save credentials locally",
                "Run OAuth flow to get token",
            ]
        return ["Set up authentication", "Configure API access"]

    def _get_execution_steps(self, intent: ParsedIntent) -> List[str]:
        """Get execution steps based on intent."""
        if intent.action in {"get_calendar_events", "calendar.list_events"}:
            return [
                "Authenticate with OAuth token",
                "Call calendar list events API",
                "Parse and display results",
            ]
        elif intent.action == "create_calendar_event":
            return [
                "Authenticate with OAuth token",
                "Create event object",
                "Call calendar create event API",
            ]
        return ["Execute the requested action"]

    def _build_plan(
        self,
        request: str,
        intent: ParsedIntent,
        research: Dict[str, Any],
        creds_exist: bool,
    ) -> ExecutionPlan:
        """
        Build an execution plan using the LLM.

        The LLM creates a detailed, actionable plan based on:
        - The user's request
        - The parsed intent
        - Research findings
        - Whether credentials exist

        Falls back to hardcoded plan if LLM is unavailable.
        """
        if self._is_local_app_task(intent, request):
            return ExecutionPlan(
                request=request,
                intent=intent,
                steps=[{
                    "phase": "EXECUTE",
                    "description": request,
                    "action": "vision_guided",
                }],
                research_summary="Local app automation",
                plan_type="EXECUTE",
            )
        # Try LLM-based plan generation
        llm_plan = self._build_plan_with_llm(request, intent, research, creds_exist)
        if llm_plan:
            return llm_plan

        # Fallback to hardcoded plan
        self._status("  (Using fallback plan generation)")
        return self._build_plan_fallback(request, intent, research, creds_exist)

    def _build_plan_with_llm(
        self,
        request: str,
        intent: ParsedIntent,
        research: Dict[str, Any],
        creds_exist: bool,
    ) -> Optional[ExecutionPlan]:
        """Use LLM to generate a detailed execution plan."""
        prompt = f"""You are a task planner. Create a detailed execution plan for this request.

USER REQUEST: "{request}"

PARSED INTENT:
- Action: {intent.action}
- Service: {intent.service}
- Auth provider: {intent.auth_provider}
- Parameters: {json.dumps(intent.parameters)}

RESEARCH FINDINGS:
{research.get('summary', 'No research available')}
RESEARCH SOURCES:
{json.dumps(research.get('sources', []))}
RESEARCH SETUP STEPS:
{json.dumps(research.get('setup_steps', []))}
RESEARCH EXECUTION STEPS:
{json.dumps(research.get('execution_steps', []))}
SUCCESS CHECKS:
{json.dumps(research.get('success_checks', []))}
RESEARCH CAVEATS:
{json.dumps(research.get('caveats', []))}

  CURRENT STATE:
- Credentials exist: {creds_exist}
- Needs authentication: {intent.needs_auth}

IMPORTANT RULES:
1. If credentials don't exist and auth is needed, set plan_type="SETUP_GUIDE"
2. SETUP_GUIDE plans must contain manual setup steps only (no open_browser or vision_guided)
3. Use "api_call" only when credentials exist
4. Each step should be specific and actionable

Create a plan with these phases:
- SETUP: Authentication and credential setup (if needed)
- EXECUTE: The actual task
- VERIFY: Confirm success (optional)

Return a JSON object with the plan."""

        result = self._call_llm_json(prompt, PLAN_SCHEMA, timeout=45, model_cls=PlanPayload)

        if not result or "error" in result:
            return None

        return self._plan_from_payload(
            request=request,
            intent=intent,
            payload=result,
            default_summary=research.get("summary"),
        )

    def _plan_from_payload(
        self,
        *,
        request: str,
        intent: ParsedIntent,
        payload: Dict[str, Any],
        default_summary: Optional[str] = None,
    ) -> Optional[ExecutionPlan]:
        """Build ExecutionPlan from a validated payload dict."""
        try:
            steps = payload.get("steps", [])

            validated_steps = []
            for step in steps:
                validated_steps.append({
                    "phase": step.get("phase", "EXECUTE"),
                    "description": step.get("description", ""),
                    "action": step.get("action", "vision_guided"),
                    "url": step.get("url", ""),
                    "details": step.get("details", ""),
                })

            return ExecutionPlan(
                request=request,
                intent=intent,
                steps=validated_steps,
                research_summary=payload.get("summary", default_summary),
                plan_type=payload.get("plan_type", "EXECUTE"),
            )
        except Exception as e:
            logger.warning(f"Could not create plan from LLM result: {e}")
            return None

    def _build_plan_fallback(
        self,
        request: str,
        intent: ParsedIntent,
        research: Dict[str, Any],
        creds_exist: bool,
    ) -> ExecutionPlan:
        """Fallback hardcoded plan generation."""
        steps = []
        plan_type = "EXECUTE"

        # If we need to set up credentials
        if not creds_exist and intent.needs_auth:
            plan_type = "SETUP_GUIDE"
            setup_steps = research.get("setup_steps") or self._get_setup_steps(intent)
            for step_desc in setup_steps:
                steps.append({
                    "phase": "SETUP",
                    "description": step_desc,
                    "action": "manual",
                })

        # Add execution steps
        for step_desc in research.get("execution_steps", []):
            steps.append({
                "phase": "EXECUTE",
                "description": step_desc,
                "action": "api_call" if creds_exist else "vision_guided",
            })

        return ExecutionPlan(
            request=request,
            intent=intent,
            steps=steps,
            research_summary=research.get("summary"),
            plan_type=plan_type,
        )

    def _execute_plan(self, plan: ExecutionPlan) -> TaskResult:
        """Execute the plan step by step."""
        steps_completed = 0
        replan_attempts = 0
        max_replans = 2
        step_index = 0

        while step_index < len(plan.steps):
            step = plan.steps[step_index]
            self._status(f"\n  Executing step {step_index + 1}/{len(plan.steps)}: {step['description']}")

            action = step.get("action", "vision_guided")
            success = True
            message = ""

            if action == "open_browser":
                url = step.get("url", "")
                success, message = self._open_browser(url)
                if success:
                    self._status(f"    [OK] Opened browser to {url}")
                    time.sleep(3)  # Wait for browser to load
                    steps_completed += 1

            elif action == "vision_guided":
                last_ui: Dict[str, Any] = {"screenshot": None, "analysis": None}

                def _on_step(s: Dict[str, Any]) -> None:
                    last_ui["screenshot"] = s.get("screenshot")
                    last_ui["analysis"] = s.get("analysis")
                    self._status(
                        f"    [{s.get('method', 'Hybrid')}] {s.get('action', {}).get('reasoning', '')[:80]}"
                    )

                def _ask_user_ui(question: str) -> str:
                    answer = self._ask_user(question)
                    self._store_ui_lesson(
                        objective=step["description"],
                        plan_summary=plan.research_summary or "",
                        question=question,
                        answer=answer,
                        ui_state=last_ui,
                    )
                    return answer

                result = self.executor.run_task(
                    objective=step["description"],
                    context=f"Plan: {plan.research_summary}\nCurrent step: {step['description']}",
                    on_step=_on_step,
                    on_user_input=_ask_user_ui,
                )

                if not result["success"]:
                    if result.get("summary", "").startswith("Need user input"):
                        continue
                    success = False
                    message = result.get("summary") or "Execution failed"
                else:
                    steps_completed += 1

            elif action == "api_call":
                success, message = self._execute_api_step(plan.intent, step)
                if success:
                    self._status(f"    [OK] {message}")
                    steps_completed += 1

            elif action == "wait":
                time.sleep(2)
                steps_completed += 1
                message = "Waited"

            elif action == "manual":
                if self._is_local_app_task(plan.intent, plan.request):
                    last_ui: Dict[str, Any] = {"screenshot": None, "analysis": None}

                    def _on_step(s: Dict[str, Any]) -> None:
                        last_ui["screenshot"] = s.get("screenshot")
                        last_ui["analysis"] = s.get("analysis")
                        self._status(
                            f"    [{s.get('method', 'Hybrid')}] {s.get('action', {}).get('reasoning', '')[:80]}"
                        )

                    def _ask_user_ui(question: str) -> str:
                        answer = self._ask_user(question)
                        self._store_ui_lesson(
                            objective=step["description"],
                            plan_summary=plan.research_summary or "",
                            question=question,
                            answer=answer,
                            ui_state=last_ui,
                        )
                        return answer

                    result = self.executor.run_task(
                        objective=step["description"],
                        context=f"Plan: {plan.research_summary}\nCurrent step: {step['description']}",
                        on_step=_on_step,
                        on_user_input=_ask_user_ui,
                    )
                    if not result["success"]:
                        if result.get("summary", "").startswith("Need user input"):
                            continue
                        success = False
                        message = result.get("summary") or "Execution failed"
                    else:
                        steps_completed += 1
                else:
                    user_confirm = self._ask_user(
                        f"Please complete this step and confirm: {step['description']} (done/skip)"
                    )
                    if user_confirm.lower() in ("done", "d", "yes", "y"):
                        steps_completed += 1
                        message = "Manual step confirmed"
                    else:
                        success = False
                        message = "Manual step not confirmed"

            else:
                success = False
                message = f"Unknown action type: {action}"

            if success:
                step_index += 1
                time.sleep(0.5)
                continue

            # ============================================================
            # STOP - THINK - REPLAN
            # ============================================================
            reflection = self._reflect_on_step_failure(plan, step, message)
            self._save_step_reflexion(plan, step, message, reflection)

            if replan_attempts < max_replans:
                new_plan = self._replan_after_step_failure(plan, step, message, reflection)
                if new_plan:
                    replan_attempts += 1
                    plan = new_plan
                    if plan.plan_type == "SETUP_GUIDE":
                        self._status("\n" + "=" * 50)
                        self._status("SETUP GUIDE")
                        self._status("=" * 50)
                        for idx, step_info in enumerate(plan.steps, 1):
                            self._status(f"  {idx}. [{step_info['phase']}] {step_info['description']}")
                        self._status("=" * 50 + "\n")
                        return TaskResult(
                            success=False,
                            summary="Setup required. Follow the steps above and re-run your request.",
                            steps_taken=steps_completed,
                            error=message,
                        )
                    steps_completed = 0
                    step_index = 0
                    self._status("  [REPLAN] New plan generated after failure")
                    continue

            return TaskResult(
                success=False,
                summary=f"Execution failed: {message}",
                steps_taken=steps_completed,
                error=message,
            )

        return TaskResult(
            success=True,
            summary=f"Completed {steps_completed} steps successfully",
            steps_taken=steps_completed,
        )

    def _reflect_on_step_failure(
        self,
        plan: ExecutionPlan,
        step: Dict[str, Any],
        error: str,
    ) -> str:
        """Analyze why a plan step failed to inform replanning."""
        prompt = f"""A plan step failed during execution. Analyze WHY it failed.

PLAN SUMMARY: {plan.research_summary}
FAILED STEP: {step.get('description')}
ACTION: {step.get('action')}
ERROR: {error}

Respond with:
1. ROOT CAUSE
2. LESSON
3. SUGGESTION

Keep it concise and actionable (<= 150 words)."""

        response = self._call_llm_chat(prompt, timeout=20)
        if response:
            return response
        return f"Step '{step.get('description')}' failed with error: {error}"

    def _replan_after_step_failure(
        self,
        plan: ExecutionPlan,
        step: Dict[str, Any],
        error: str,
        reflection: str,
    ) -> Optional[ExecutionPlan]:
        """Generate a revised plan after a failed step."""
        creds_exist = self._check_credentials(plan.intent.auth_provider)
        prompt = f"""A plan step failed. Create a NEW plan to achieve the objective.

REQUEST: "{plan.request}"
FAILED STEP: {step.get('description')}
ERROR: {error}
ANALYSIS: {reflection}

CURRENT INTENT:
- Action: {plan.intent.action}
- Service: {plan.intent.service}
- Auth provider: {plan.intent.auth_provider}
- Parameters: {json.dumps(plan.intent.parameters)}

CURRENT STATE:
- Credentials exist: {creds_exist}

IMPORTANT RULES:
1. If credentials don't exist and auth is needed, set plan_type="SETUP_GUIDE"
2. SETUP_GUIDE plans must contain manual setup steps only (no open_browser or vision_guided)
3. Use "api_call" only when credentials exist
4. Each step should be specific and actionable

Return a JSON object with the plan."""

        payload = self._call_llm_json(prompt, PLAN_SCHEMA, timeout=45, model_cls=PlanPayload)
        if not payload or "error" in payload:
            return None

        return self._plan_from_payload(
            request=plan.request,
            intent=plan.intent,
            payload=payload,
            default_summary=plan.research_summary,
        )

    def _save_step_reflexion(
        self,
        plan: ExecutionPlan,
        step: Dict[str, Any],
        error: str,
        reflection: str,
    ) -> None:
        """Persist step failure in reflexion memory for future runs."""
        try:
            from agent.autonomous.memory.reflexion import ReflexionEntry, write_reflexion
            from uuid import uuid4
            from datetime import datetime, timezone

            entry = ReflexionEntry(
                id=f"learn_{uuid4().hex[:8]}",
                timestamp=datetime.now(timezone.utc).isoformat(),
                objective=plan.request,
                context_fingerprint=f"plan_step_{step.get('action', 'unknown')}",
                phase="execution",
                tool_calls=[{
                    "action": step.get("action"),
                    "description": step.get("description"),
                }],
                errors=[error],
                reflection=reflection,
                fix="Replanned after step failure",
                outcome="failure",
                tags=["learning_agent", step.get("action", "unknown")],
            )
            write_reflexion(entry)
        except Exception as exc:
            logger.warning(f"Could not save step reflexion: {exc}")

    def _open_browser(self, url: str) -> Tuple[bool, str]:
        """Open a URL in Chrome (so we can see it with vision)."""
        try:
            # Find Chrome
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                shutil.which("chrome"),
                shutil.which("google-chrome"),
            ]
            chrome = next((p for p in chrome_paths if p and os.path.exists(p)), None)

            if chrome:
                subprocess.Popen([chrome, url])
            else:
                # Fallback to default browser
                webbrowser.open(url)

            return True, f"Opened {url}"
        except Exception as e:
            return False, str(e)

    def _execute_api_step(self, intent: ParsedIntent, step: Dict[str, Any]) -> Tuple[bool, str]:
        """Execute an API call step directly."""
        if intent.auth_provider == "google" and intent.action in {"get_calendar_events", "calendar.list_events"}:
            try:
                from agent.tools.calendar import get_calendar_events, CalendarEventsArgs
                from datetime import date, timedelta

                # Determine time range
                time_range = intent.parameters.get("time_range", "tomorrow")
                if time_range == "tomorrow":
                    start = date.today() + timedelta(days=1)
                    end = start + timedelta(days=1)
                elif time_range == "today":
                    start = date.today()
                    end = start + timedelta(days=1)
                else:
                    start = date.today()
                    end = start + timedelta(days=7)

                args = CalendarEventsArgs(
                    start_date=start.isoformat(),
                    end_date=end.isoformat(),
                )
                result = get_calendar_events(None, args)

                if result.get("success"):
                    events = result.get("events", [])
                    if events:
                        return True, f"Found {len(events)} events: {', '.join(e.get('summary', 'Untitled') for e in events[:3])}"
                    else:
                        return True, "No events found for the requested time period"
                else:
                    return False, result.get("error", "API call failed")

            except Exception as e:
                return False, str(e)

        return True, f"Executed: {step['description']}"

    def _execute_skill(self, skill, original_request: str) -> TaskResult:
        """Execute a known skill."""
        self._status(f"Executing known skill: {skill.name}")

        # Deterministic Notepad flow (file-based, avoids UI typing errors)
        if self._should_use_notepad_file(skill, original_request):
            success, msg, evidence = self._execute_notepad_file(original_request)
            self.skill_library.record_outcome(skill.id, success=success, notes=None if success else msg)
            if evidence.get("verification_warning"):
                self._record_verification_warning(
                    skill,
                    original_request,
                    str(evidence.get("verification_warning")),
                    evidence,
                )
            if not success:
                self._record_verification_failure(skill, original_request, msg, evidence)
            return TaskResult(
                success=success,
                summary=msg,
                steps_taken=1 if success else 0,
                skill_used=skill.id,
                evidence=evidence or {},
            )

        # Check prerequisites
        if skill.requires_auth:
            if not self._check_credentials(skill.requires_auth):
                self._status(f"Need to set up {skill.requires_auth} authentication first")
                # Trigger the full flow to set up auth
                return self.run(original_request)

        # Execute the skill steps
        try:
            steps_completed = 0
            for step in skill.steps:
                self._status(f"  Step: {step.description}")

                if step.action == "api_call":
                    intent = ParsedIntent(
                        action="calendar.list_events",
                        service=skill.tags[0] if skill.tags else None,
                        auth_provider=skill.requires_auth,
                    )
                    success, msg = self._execute_api_step(intent, {"description": step.description})
                    if not success and not step.optional:
                        raise Exception(msg)
                    self._status(f"    [OK] {msg}")
                elif step.action == "open_browser":
                    url = step.target or step.value or ""
                    success, msg = self._open_browser(url)
                    if not success and not step.optional:
                        raise Exception(msg or "Failed to open browser")
                    if msg:
                        self._status(f"    [OK] {msg}")
                elif step.action == "vision_guided":
                    result = self.executor.run_task(
                        objective=step.description,
                        context=f"Skill: {skill.name}",
                        on_step=lambda s: self._status(
                            f"    [{s.get('method', 'Hybrid')}] {s.get('action', {}).get('reasoning', '')[:80]}"
                        ),
                        on_user_input=self._ask_user,
                    )
                    if not result["success"]:
                        msg = result.get("summary") or "Execution failed"
                        if not step.optional:
                            raise Exception(msg)
                        continue
                    steps_completed += 1
                    continue
                elif step.action == "manual":
                    user_confirm = self._ask_user(
                        f"Please complete this step and confirm: {step.description} (done/skip)"
                    )
                    if user_confirm.lower() in ("done", "d", "yes", "y"):
                        steps_completed += 1
                        continue
                    if step.optional:
                        continue
                    raise Exception("Manual step not confirmed")
                elif step.action == "wait":
                    time.sleep(2)
                else:
                    if step.optional:
                        continue
                    raise Exception(f"Unknown action type: {step.action}")

                steps_completed += 1

            self.skill_library.record_outcome(skill.id, success=True)
            return TaskResult(
                success=True,
                summary=f"Completed skill: {skill.name}",
                steps_taken=steps_completed,
                skill_used=skill.id,
            )

        except Exception as e:
            self.skill_library.record_outcome(skill.id, success=False, notes=str(e))
            return TaskResult(
                success=False,
                summary=f"Skill failed: {e}",
                error=str(e),
                skill_used=skill.id,
            )

    def _save_learned_skill(
        self,
        request: str,
        intent: ParsedIntent,
        plan: ExecutionPlan,
        result: TaskResult,
    ) -> str:
        """Save a successful execution as a new skill."""
        from agent.autonomous.skill_library import Skill, SkillStep

        # Generate skill name
        words = request.lower().split()[:5]
        skill_name = "_".join(w for w in words if w.isalnum())

        # Create skill steps
        skill_steps = []
        for step in plan.steps:
            skill_steps.append(SkillStep(
                action=step.get("action", "vision_guided"),
                description=step.get("description", ""),
                target=step.get("url"),
            ))

        # Extract tags
        tags = []
        if intent.service:
            tags.append(intent.service)
        if intent.auth_provider:
            tags.append(intent.auth_provider)
        if intent.action:
            tags.append(intent.action)

        skill = Skill(
            name=skill_name,
            description=f"{request}. Uses {intent.service or 'automation'}.",
            tags=tags,
            steps=skill_steps,
            requires_auth=intent.auth_provider,
            source="learned",
            learned_from_task=request,
        )

        return self.skill_library.save(skill)

    def _log_failure(
        self,
        request: str,
        intent: ParsedIntent,
        plan: ExecutionPlan,
        result: TaskResult,
    ) -> None:
        """Log a failure to reflexion for learning."""
        try:
            from agent.autonomous.memory.reflexion import ReflexionEntry, write_reflexion

            entry = ReflexionEntry(
                id=f"learning_{uuid4().hex[:8]}",
                timestamp=datetime.now(timezone.utc).isoformat(),
                objective=request,
                context_fingerprint=f"learning_{intent.service or 'unknown'}",
                phase="execution",
                tool_calls=[{
                    "intent": intent.model_dump(),
                    "plan_steps": len(plan.steps),
                }],
                errors=[result.error or result.summary],
                reflection=f"Failed: {request}. Error: {result.error}",
                fix=f"Need to investigate: {result.summary}",
                outcome="failure",
                tags=list(set([intent.service, intent.auth_provider, intent.action])) if intent.service else ["unknown"],
            )
            write_reflexion(entry)
        except Exception as e:
            logger.warning(f"Could not log to reflexion: {e}")

    def _record_verification_failure(
        self,
        skill,
        request: str,
        error: str,
        evidence: Dict[str, Any],
    ) -> None:
        """Record verification failure into memory/reflexion."""
        try:
            if self.memory_store:
                payload = {
                    "task": request,
                    "skill": getattr(skill, "name", "unknown"),
                    "error": error,
                    "evidence": evidence,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                self.memory_store.upsert(
                    kind="experience",
                    key=f"verify:{getattr(skill, 'id', 'unknown')}",
                    content=json.dumps(payload, ensure_ascii=False),
                    metadata={"source": "verification"},
                )
        except Exception:
            pass

    def _record_verification_warning(
        self,
        skill,
        request: str,
        warning: str,
        evidence: Dict[str, Any],
    ) -> None:
        """Record verification warning into memory/reflexion."""
        try:
            if self.memory_store:
                payload = {
                    "task": request,
                    "skill": getattr(skill, "name", "unknown"),
                    "warning": warning,
                    "evidence": evidence,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                self.memory_store.upsert(
                    kind="experience",
                    key=f"verify_warning:{getattr(skill, 'id', 'unknown')}",
                    content=json.dumps(payload, ensure_ascii=False),
                    metadata={"source": "verification", "severity": "warning"},
                )
        except Exception:
            pass

        try:
            from agent.autonomous.memory.reflexion import ReflexionEntry, write_reflexion
            entry = ReflexionEntry(
                id=f"verify_warn_{uuid4().hex[:8]}",
                timestamp=datetime.now(timezone.utc).isoformat(),
                objective=request,
                context_fingerprint=f"verify_warn_{getattr(skill, 'name', 'unknown')}",
                phase="verification",
                tool_calls=[{"skill": getattr(skill, "name", "unknown")}],
                errors=[warning],
                reflection=(
                    f"Verification warning for skill {getattr(skill, 'name', 'unknown')}: {warning}"
                ),
                fix="Enable UI text capture or OCR, or install UI automation deps for stronger verification.",
                outcome="warning",
                tags=list(set([getattr(skill, 'name', 'unknown'), 'verification'])),
            )
            write_reflexion(entry)
        except Exception:
            pass

        # Note: This method only records warnings, not failures.
        # Failures would be recorded elsewhere with proper error context.


# Singleton instance
_agent: Optional[LearningAgent] = None


def get_learning_agent(llm=None) -> LearningAgent:
    """Get the singleton learning agent instance."""
    global _agent
    if _agent is None:
        _agent = LearningAgent(llm)
    return _agent


__all__ = [
    "LearningAgent",
    "TaskResult",
    "ParsedIntent",
    "ExecutionPlan",
    "get_learning_agent",
]
