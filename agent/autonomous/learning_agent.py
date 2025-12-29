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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field

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
            "description": "The action to perform (e.g., get_calendar_events, send_email, create_event)"
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
                    "action": {"type": "string", "enum": ["open_browser", "vision_guided", "api_call", "wait"]},
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
    "required": ["summary", "steps"]
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
    action: str  # e.g., "get_calendar_events", "send_email", "search_web"
    service: Optional[str] = None  # e.g., "google_calendar", "outlook", "gmail"
    parameters: Dict[str, Any] = Field(default_factory=dict)
    needs_auth: bool = False
    auth_provider: Optional[str] = None  # "google", "microsoft"
    clarifying_questions: List[str] = Field(default_factory=list)


class ExecutionPlan(BaseModel):
    """Plan for executing a task."""
    request: str
    intent: ParsedIntent
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    research_summary: Optional[str] = None
    approved: bool = False


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
            memory_path = REPO_ROOT / "agent" / "memory" / "learning_memory.db"
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
        if self.on_user_input:
            return self.on_user_input(question)
        else:
            print(f"\n  [AGENT ASKS] {question}")
            return input("  > ").strip()

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

        self._status(f"  → Action: {intent.action}")
        self._status(f"  → Service: {intent.service or 'unknown'}")
        self._status(f"  → Needs auth: {intent.needs_auth}")

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

        # ============================================================
        # STEP 2: Check local credentials and skills
        # ============================================================
        self._status("Step 2: Checking local credentials and skills...")

        # Check credentials
        creds_exist = self._check_credentials(intent.auth_provider)
        if creds_exist:
            self._status(f"  ✓ Found {intent.auth_provider} credentials")
        else:
            self._status(f"  ✗ No {intent.auth_provider} credentials found")

        # Check skill library
        matching_skills = self.skill_library.search(user_request, k=3)
        if matching_skills:
            best_skill, similarity = matching_skills[0]
            if similarity > 0.7:
                self._status(f"  ✓ Found matching skill: {best_skill.name} (confidence: {similarity:.0%})")
                if creds_exist:
                    return self._execute_skill(best_skill, user_request)
            else:
                self._status(f"  ~ Partial match: {best_skill.name} ({similarity:.0%})")
        else:
            self._status("  ✗ No matching skills found")

        # ============================================================
        # STEP 3: Research if we don't know how to do this
        # ============================================================
        if not creds_exist or not matching_skills or matching_skills[0][1] < 0.5:
            self._status("Step 3: Researching how to do this...")
            research = self._do_research(user_request, intent)

            if not research["success"]:
                return TaskResult(
                    success=False,
                    summary=f"Could not find how to do this: {research.get('error')}",
                    error=research.get("error"),
                    research_performed=True,
                )

            self._status(f"  ✓ Found approach: {research.get('summary', 'Unknown')[:100]}")
        else:
            research = {"success": True, "summary": "Using existing knowledge"}

        # ============================================================
        # STEP 4: Create plan and get user approval
        # ============================================================
        self._status("Step 4: Creating execution plan...")
        plan = self._build_plan(user_request, intent, research, creds_exist)

        self._status("\n" + "=" * 50)
        self._status("EXECUTION PLAN")
        self._status("=" * 50)
        for i, step in enumerate(plan.steps, 1):
            self._status(f"  {i}. [{step['phase']}] {step['description']}")
        self._status("=" * 50 + "\n")

        approval = self._ask_user("Do you want me to execute this plan? (yes/no)")
        if approval.lower() not in ("yes", "y"):
            return TaskResult(
                success=False,
                summary="User declined to execute plan",
                error="User cancelled",
            )

        plan.approved = True

        # ============================================================
        # STEP 5: Execute the plan
        # ============================================================
        self._status("Step 5: Executing plan...")
        result = self._execute_plan(plan)

        # ============================================================
        # STEP 6: Save and learn
        # ============================================================
        if result.success:
            self._status("Step 6: Saving successful procedure as skill...")
            skill_id = self._save_learned_skill(user_request, intent, plan, result)
            result.skill_learned = skill_id
            self._status(f"  ✓ Saved skill: {skill_id}")
        else:
            self._status("Step 6: Logging failure for learning...")
            self._log_failure(user_request, intent, plan, result)
            self._status("  ✓ Failure logged to reflexion")

        return result

    def _get_llm(self):
        """Get or create an LLM client for reasoning."""
        if self.llm:
            return self.llm

        # Try Codex first
        try:
            from agent.llm.codex_cli_client import CodexCliClient
            self.llm = CodexCliClient.from_env()
            # Quick test to see if it's authenticated
            return self.llm
        except Exception as e:
            logger.warning(f"Codex CLI not available: {e}")

        # Fall back to OpenRouter
        try:
            from agent.llm.openrouter_client import OpenRouterClient
            self.llm = OpenRouterClient.from_env()
            self._status("Using OpenRouter for LLM calls")
            return self.llm
        except Exception as e:
            logger.warning(f"OpenRouter not available: {e}")

        return None

    def _call_llm_json(self, prompt: str, schema: Dict[str, Any], timeout: int = 60) -> Optional[Dict[str, Any]]:
        """Call LLM and get structured JSON output."""
        llm = self._get_llm()
        if not llm:
            return None

        try:
            # Write schema to temp file
            schema_path = Path(tempfile.gettempdir()) / f"schema_{uuid4().hex[:8]}.json"
            schema_path.write_text(json.dumps(schema), encoding="utf-8")

            # Use reason_json for structured output - pass Path object, not string
            result = llm.reason_json(prompt, schema_path=schema_path, timeout_seconds=timeout)

            # Clean up
            try:
                schema_path.unlink()
            except Exception:
                pass

            return result
        except Exception as e:
            # If Codex failed, try OpenRouter as fallback
            if "not authenticated" in str(e).lower() or "codex" in str(e).lower():
                logger.warning(f"Codex failed, trying OpenRouter: {e}")
                try:
                    from agent.llm.openrouter_client import OpenRouterClient
                    fallback_llm = OpenRouterClient.from_env()
                    result = fallback_llm.reason_json(prompt, schema_path=schema_path, timeout_seconds=timeout)
                    try:
                        schema_path.unlink()
                    except Exception:
                        pass
                    return result
                except Exception as fallback_e:
                    logger.error(f"OpenRouter fallback also failed: {fallback_e}")
            else:
                logger.error(f"LLM call failed: {e}")
            return None

    def _call_llm_chat(self, prompt: str, timeout: int = 60) -> Optional[str]:
        """Call LLM for free-form chat."""
        llm = self._get_llm()
        if not llm:
            return None

        try:
            # OpenRouter uses different signature
            if hasattr(llm, 'chat'):
                try:
                    return llm.chat(prompt, timeout_seconds=timeout)
                except TypeError:
                    # OpenRouter doesn't take timeout_seconds
                    return llm.chat(prompt)
            return None
        except Exception as e:
            # Try OpenRouter fallback
            if "not authenticated" in str(e).lower() or "codex" in str(e).lower():
                try:
                    from agent.llm.openrouter_client import OpenRouterClient
                    fallback_llm = OpenRouterClient.from_env()
                    return fallback_llm.chat(prompt)
                except Exception:
                    pass
            logger.error(f"LLM chat failed: {e}")
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
1. What action they want (e.g., get_calendar_events, send_email, create_event, search_web, open_app)
2. What service is needed (e.g., google_calendar, outlook, gmail, notion, slack)
3. What authentication provider is needed (google, microsoft, or null if none)
4. Whether authentication is required
5. Extract any parameters (time ranges, dates, recipients, subjects)
6. If anything is ambiguous, list clarifying questions to ask

Be specific about the service. If they mention "calendar" without specifying which one, ask which service they use.
If they mention "tomorrow" or "today", extract that as a time_range parameter.

Return a JSON object matching the schema."""

        result = self._call_llm_json(prompt, INTENT_SCHEMA, timeout=30)

        if not result:
            return None

        # Check for errors
        if "error" in result:
            logger.warning(f"LLM intent parsing error: {result.get('error')}")
            return None

        try:
            return ParsedIntent(
                action=result.get("action", "unknown"),
                service=result.get("service"),
                parameters=result.get("parameters", {}),
                needs_auth=result.get("needs_auth", False),
                auth_provider=result.get("auth_provider"),
                clarifying_questions=result.get("clarifying_questions", []),
            )
        except Exception as e:
            logger.warning(f"Could not create ParsedIntent from LLM result: {e}")
            return None

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
                action = "get_calendar_events"
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
            action=action,
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
            token_path = CREDENTIALS_DIR / "token.json"
            creds_path = CREDENTIALS_DIR / "credentials.json"
            return token_path.exists() or creds_path.exists()
        elif provider == "microsoft":
            # TODO: Check Microsoft credentials
            return False
        return False

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

        if intent.action == "get_calendar_events":
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

            self._status(f"  Searching: {query}")

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
                self._status(f"  Search failed: {search_result.error}")
                return self._fallback_research(intent)

            results = search_result.output.get("results", [])
            if not results:
                return self._fallback_research(intent)

            # Fetch and summarize top results
            summaries = []
            for result in results[:3]:
                url = result.get("url", "")
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                summaries.append(f"- {title}: {snippet[:200]}")

            # Build research summary
            summary = self._build_research_summary(intent, summaries)

            return {
                "success": True,
                "summary": summary,
                "service": intent.service,
                "auth_provider": intent.auth_provider,
                "setup_steps": self._get_setup_steps(intent),
                "execution_steps": self._get_execution_steps(intent),
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
            return [
                "Open Google Cloud Console in browser",
                "Create or select a project",
                "Enable Google Calendar API",
                "Configure OAuth consent screen",
                "Create OAuth 2.0 credentials",
                "Download credentials.json",
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
        if intent.action == "get_calendar_events":
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

CURRENT STATE:
- Credentials exist: {creds_exist}
- Needs authentication: {intent.needs_auth}

IMPORTANT RULES:
1. If credentials don't exist and auth is needed, the FIRST step must be "open_browser" to the appropriate console:
   - For Google: https://console.cloud.google.com/
   - For Microsoft: https://portal.azure.com/
2. Browser must be opened BEFORE any vision_guided steps can work
3. Use "vision_guided" for steps that require looking at and interacting with a browser
4. Use "api_call" for steps that can be done programmatically (only if creds exist)
5. Each step should be specific and actionable

Create a plan with these phases:
- SETUP: Authentication and credential setup (if needed)
- EXECUTE: The actual task
- VERIFY: Confirm success (optional)

Return a JSON object with the plan."""

        result = self._call_llm_json(prompt, PLAN_SCHEMA, timeout=45)

        if not result or "error" in result:
            return None

        try:
            steps = result.get("steps", [])

            # Validate and convert steps
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
                research_summary=result.get("summary", research.get("summary")),
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

        # If we need to set up credentials
        if not creds_exist and intent.needs_auth:
            # First step: OPEN BROWSER
            browser_step_desc = None
            if intent.auth_provider == "google":
                browser_step_desc = "Open Google Cloud Console in browser"
                steps.append({
                    "phase": "SETUP",
                    "description": browser_step_desc,
                    "action": "open_browser",
                    "url": "https://console.cloud.google.com/",
                })
            elif intent.auth_provider == "microsoft":
                browser_step_desc = "Open Azure Portal in browser"
                steps.append({
                    "phase": "SETUP",
                    "description": browser_step_desc,
                    "action": "open_browser",
                    "url": "https://portal.azure.com/",
                })

            # Add setup steps from research, skipping the browser open step to avoid duplication
            for step_desc in research.get("setup_steps", []):
                # Skip if this is the same as the browser step we already added
                if browser_step_desc and step_desc.lower().startswith("open"):
                    if "console" in step_desc.lower() or "portal" in step_desc.lower():
                        continue
                steps.append({
                    "phase": "SETUP",
                    "description": step_desc,
                    "action": "vision_guided",
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
        )

    def _execute_plan(self, plan: ExecutionPlan) -> TaskResult:
        """Execute the plan step by step."""
        steps_completed = 0

        for i, step in enumerate(plan.steps):
            self._status(f"\n  Executing step {i+1}/{len(plan.steps)}: {step['description']}")

            action = step.get("action", "vision_guided")

            if action == "open_browser":
                # CRITICAL: Open browser FIRST so vision can see it
                url = step.get("url", "")
                success, msg = self._open_browser(url)
                if not success:
                    return TaskResult(
                        success=False,
                        summary=f"Failed to open browser: {msg}",
                        steps_taken=steps_completed,
                        error=msg,
                    )
                self._status(f"    ✓ Opened browser to {url}")
                time.sleep(3)  # Wait for browser to load
                steps_completed += 1

            elif action == "vision_guided":
                # Use hybrid executor (UI automation + vision fallback)
                # This is MUCH better than vision-only
                result = self.executor.run_task(
                    objective=step["description"],
                    context=f"Plan: {plan.research_summary}\nCurrent step: {step['description']}",
                    on_step=lambda s: self._status(f"    [{s.get('method', 'Hybrid')}] {s.get('action', {}).get('reasoning', '')[:80]}"),
                    on_user_input=self._ask_user,
                )

                if not result["success"]:
                    # Check if it's just asking for user input
                    if result.get("summary", "").startswith("Need user input"):
                        continue
                    return TaskResult(
                        success=False,
                        summary=f"Execution failed: {result.get('summary')}",
                        steps_taken=steps_completed,
                        error=result.get("summary"),
                    )
                steps_completed += 1

            elif action == "api_call":
                # Direct API call (credentials exist)
                success, msg = self._execute_api_step(plan.intent, step)
                if not success:
                    return TaskResult(
                        success=False,
                        summary=f"API call failed: {msg}",
                        steps_taken=steps_completed,
                        error=msg,
                    )
                self._status(f"    ✓ {msg}")
                steps_completed += 1

            time.sleep(0.5)

        return TaskResult(
            success=True,
            summary=f"Completed {steps_completed} steps successfully",
            steps_taken=steps_completed,
        )

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
        if intent.auth_provider == "google" and intent.action == "get_calendar_events":
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
                        action="get_calendar_events",
                        service=skill.tags[0] if skill.tags else None,
                        auth_provider=skill.requires_auth,
                    )
                    success, msg = self._execute_api_step(intent, {"description": step.description})
                    if not success and not step.optional:
                        raise Exception(msg)
                    self._status(f"    ✓ {msg}")

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
