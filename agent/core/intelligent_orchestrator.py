"""
Intelligent Orchestrator - LLM-based strategy selection.

This replaces brittle keyword-based routing with true semantic understanding.
The LLM analyzes the user request and decides:
1. What capabilities are needed (tools, web, planning, etc.)
2. Risk level of the operation
3. Which skill/tool is most appropriate
4. Whether clarification is needed

This is the "brain" that decides HOW to handle a request.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# Strategy Schema
# =============================================================================

class RiskLevel(str, Enum):
    """Risk level of an operation."""
    NONE = "none"           # Read-only, no side effects
    LOW = "low"             # Minor side effects, easily reversible
    MEDIUM = "medium"       # Significant changes, may need confirmation
    HIGH = "high"           # Destructive or irreversible, requires approval


class Complexity(str, Enum):
    """Complexity of the task."""
    SIMPLE = "simple"       # Single tool call
    MODERATE = "moderate"   # Few steps, straightforward
    COMPLEX = "complex"     # Multi-step, requires planning


class Strategy(BaseModel):
    """
    The orchestrator's decision about how to handle a request.

    This is the output of the LLM analysis - it tells the agent
    what capabilities and approach to use.
    """
    # What's needed
    needs_tools: bool = Field(
        default=True,
        description="Whether tool execution is required"
    )
    needs_web: bool = Field(
        default=False,
        description="Whether web browsing is required"
    )
    needs_ui_automation: bool = Field(
        default=False,
        description="Whether desktop UI automation is required"
    )
    needs_deep_planning: bool = Field(
        default=False,
        description="Whether multi-step planning is needed"
    )
    needs_memory: bool = Field(
        default=False,
        description="Whether memory lookup is helpful"
    )

    # Assessment
    risk_level: RiskLevel = Field(
        default=RiskLevel.LOW,
        description="Risk level of the operation"
    )
    complexity: Complexity = Field(
        default=Complexity.SIMPLE,
        description="Complexity of the task"
    )

    # Routing
    preferred_skill: Optional[str] = Field(
        default=None,
        description="Most appropriate skill (calendar, browser, filesystem, etc.)"
    )
    preferred_tool: Optional[str] = Field(
        default=None,
        description="Specific tool to use if known"
    )

    # Clarification
    clarification_questions: List[str] = Field(
        default_factory=list,
        description="Questions to ask user for clarification"
    )
    confidence: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Confidence in this strategy (0-1)"
    )

    # Reasoning
    reasoning: str = Field(
        default="",
        description="Brief explanation of the strategy choice"
    )

    # Extracted info
    intent: str = Field(
        default="",
        description="Parsed intent (e.g., 'list_calendar_events')"
    )
    entities: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extracted entities (dates, names, etc.)"
    )


# Strategy JSON schema for LLM
STRATEGY_SCHEMA = {
    "type": "object",
    "properties": {
        "needs_tools": {
            "type": "boolean",
            "description": "Whether tool execution is required"
        },
        "needs_web": {
            "type": "boolean",
            "description": "Whether web browsing is required"
        },
        "needs_ui_automation": {
            "type": "boolean",
            "description": "Whether desktop UI automation is required"
        },
        "needs_deep_planning": {
            "type": "boolean",
            "description": "Whether multi-step planning is needed"
        },
        "needs_memory": {
            "type": "boolean",
            "description": "Whether memory lookup would be helpful"
        },
        "risk_level": {
            "type": "string",
            "enum": ["none", "low", "medium", "high"],
            "description": "Risk level: none=read-only, low=reversible, medium=significant, high=destructive"
        },
        "complexity": {
            "type": "string",
            "enum": ["simple", "moderate", "complex"],
            "description": "Task complexity"
        },
        "preferred_skill": {
            "type": "string",
            "description": "Most appropriate skill (calendar, browser, filesystem, shell, python, api, or null)"
        },
        "preferred_tool": {
            "type": "string",
            "description": "Specific tool to use if known"
        },
        "clarification_questions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Questions to ask user if request is ambiguous"
        },
        "confidence": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
            "description": "Confidence in this strategy (0-1)"
        },
        "reasoning": {
            "type": "string",
            "description": "Brief explanation of why this strategy was chosen"
        },
        "intent": {
            "type": "string",
            "description": "Parsed intent (e.g., 'list_calendar_events', 'create_file')"
        },
        "entities": {
            "type": "object",
            "description": "Extracted entities like dates, filenames, etc."
        }
    },
    "required": ["needs_tools", "risk_level", "complexity", "reasoning", "intent"]
}


# =============================================================================
# Intelligent Orchestrator
# =============================================================================

class IntelligentOrchestrator:
    """
    LLM-based orchestrator that analyzes requests and decides on strategy.

    This replaces keyword-based routing with true semantic understanding.
    """

    def __init__(self, llm_client=None):
        """
        Initialize the orchestrator.

        Args:
            llm_client: LLM client to use. If None, will get from adapters.
        """
        self._llm = llm_client
        self._available_skills = [
            "calendar",      # Google Calendar operations
            "browser",       # Web browsing and automation
            "filesystem",    # File operations
            "shell",         # Shell command execution
            "python",        # Python code execution
            "api",           # HTTP API calls
            "desktop",       # Desktop UI automation
            "vision",        # Screenshot and vision analysis
            "memory",        # Agent memory operations
        ]

    def _get_llm(self):
        """Get or create LLM client."""
        if self._llm is None:
            from agent.adapters import get_llm_client
            self._llm = get_llm_client()
        return self._llm

    def analyze(
        self,
        request: str,
        context: Optional[str] = None,
        available_tools: Optional[List[str]] = None,
    ) -> Strategy:
        """
        Analyze a user request and determine the best strategy.

        Args:
            request: The user's request text
            context: Optional additional context
            available_tools: List of available tool names

        Returns:
            Strategy object with the recommended approach
        """
        # First try quick pattern matching for very common cases
        quick_strategy = self._quick_match(request)
        if quick_strategy:
            logger.debug(f"Quick match: {quick_strategy.intent}")
            return quick_strategy

        # Use LLM for semantic analysis
        return self._llm_analyze(request, context, available_tools)

    def _quick_match(self, request: str) -> Optional[Strategy]:
        """
        Quick pattern matching for extremely common requests.

        This avoids LLM calls for simple, unambiguous requests.
        Returns None if LLM analysis is needed.
        """
        lower = request.lower().strip()

        # Calendar - very common
        if any(phrase in lower for phrase in [
            "check my calendar",
            "what's on my calendar",
            "show my calendar",
            "my schedule",
            "my appointments",
            "what meetings",
            "calendar for today",
            "calendar for tomorrow",
        ]):
            return Strategy(
                needs_tools=True,
                needs_web=False,
                needs_deep_planning=False,
                risk_level=RiskLevel.NONE,
                complexity=Complexity.SIMPLE,
                preferred_skill="calendar",
                intent="calendar.list_events",
                reasoning="User wants to check calendar events",
                confidence=0.95,
                entities=self._extract_time_range(lower),
            )

        # File listing
        if any(phrase in lower for phrase in [
            "list files",
            "show files",
            "what files",
            "ls ",
            "dir ",
        ]):
            return Strategy(
                needs_tools=True,
                needs_web=False,
                needs_deep_planning=False,
                risk_level=RiskLevel.NONE,
                complexity=Complexity.SIMPLE,
                preferred_skill="filesystem",
                preferred_tool="list_directory",
                intent="list_files",
                reasoning="User wants to list files",
                confidence=0.9,
            )

        # Help/info requests - no tools needed
        if any(phrase in lower for phrase in [
            "help",
            "what can you do",
            "how do i",
            "explain",
        ]):
            return Strategy(
                needs_tools=False,
                needs_web=False,
                needs_deep_planning=False,
                risk_level=RiskLevel.NONE,
                complexity=Complexity.SIMPLE,
                intent="help_request",
                reasoning="User is asking for help or information",
                confidence=0.85,
            )

        # No quick match - need LLM analysis
        return None

    def _extract_time_range(self, text: str) -> Dict[str, Any]:
        """Extract time-related entities from text."""
        entities = {}

        if "today" in text:
            entities["time_range"] = "today"
        elif "tomorrow" in text:
            entities["time_range"] = "tomorrow"
        elif "this week" in text:
            entities["time_range"] = "this_week"
        elif "next week" in text:
            entities["time_range"] = "next_week"

        return entities

    def _llm_analyze(
        self,
        request: str,
        context: Optional[str],
        available_tools: Optional[List[str]],
    ) -> Strategy:
        """
        Use LLM to analyze the request and determine strategy.
        """
        llm = self._get_llm()

        skills_desc = ", ".join(self._available_skills)
        tools_desc = ", ".join(available_tools) if available_tools else "standard tools"

        system_prompt = f"""You are an intelligent task orchestrator. Analyze user requests and determine the best strategy to handle them.

Available skills: {skills_desc}
Available tools: {tools_desc}

Your job is to:
1. Understand what the user wants to accomplish
2. Identify what capabilities are needed (tools, web, planning, etc.)
3. Assess the risk level (none=read-only, low=reversible, medium=significant changes, high=destructive/irreversible)
4. Determine complexity (simple=one step, moderate=few steps, complex=requires planning)
5. Suggest the most appropriate skill/tool
6. Ask for clarification if the request is ambiguous

Respond with a JSON object matching the schema."""

        user_prompt = f"Analyze this request and determine the strategy:\n\n{request}"
        if context:
            user_prompt += f"\n\nAdditional context:\n{context}"

        try:
            result = llm.chat_json(
                user_prompt,
                system_prompt=system_prompt,
                schema=STRATEGY_SCHEMA,
                timeout=30,
            )

            # Parse into Strategy object
            return Strategy(
                needs_tools=result.get("needs_tools", True),
                needs_web=result.get("needs_web", False),
                needs_ui_automation=result.get("needs_ui_automation", False),
                needs_deep_planning=result.get("needs_deep_planning", False),
                needs_memory=result.get("needs_memory", False),
                risk_level=RiskLevel(result.get("risk_level", "low")),
                complexity=Complexity(result.get("complexity", "simple")),
                preferred_skill=result.get("preferred_skill"),
                preferred_tool=result.get("preferred_tool"),
                clarification_questions=result.get("clarification_questions", []),
                confidence=result.get("confidence", 0.8),
                reasoning=result.get("reasoning", ""),
                intent=result.get("intent", "unknown"),
                entities=result.get("entities", {}),
            )

        except Exception as e:
            logger.warning(f"LLM analysis failed: {e}, using fallback")
            return self._fallback_analyze(request)

    def _fallback_analyze(self, request: str) -> Strategy:
        """
        Fallback analysis when LLM is unavailable.

        Uses simple heuristics to determine basic strategy.
        """
        lower = request.lower()

        # Detect web-related requests
        needs_web = any(word in lower for word in [
            "search", "browse", "website", "url", "http", "google",
            "web", "online", "internet"
        ])

        # Detect UI automation
        needs_ui = any(word in lower for word in [
            "click", "type", "window", "app", "application", "desktop",
            "notepad", "calculator", "open "
        ])

        # Detect file operations
        file_related = any(word in lower for word in [
            "file", "folder", "directory", "read", "write", "create",
            "delete", "move", "copy"
        ])

        # Detect code/shell
        code_related = any(word in lower for word in [
            "run", "execute", "python", "script", "command", "shell",
            "code", "program"
        ])

        # Determine risk
        risk = RiskLevel.LOW
        if any(word in lower for word in ["delete", "remove", "destroy", "format"]):
            risk = RiskLevel.HIGH
        elif any(word in lower for word in ["modify", "change", "update", "write", "create"]):
            risk = RiskLevel.MEDIUM

        # Determine preferred skill
        skill = None
        if "calendar" in lower or "schedule" in lower or "meeting" in lower:
            skill = "calendar"
        elif needs_web:
            skill = "browser"
        elif needs_ui:
            skill = "desktop"
        elif file_related:
            skill = "filesystem"
        elif code_related:
            skill = "python" if "python" in lower else "shell"

        return Strategy(
            needs_tools=True,
            needs_web=needs_web,
            needs_ui_automation=needs_ui,
            needs_deep_planning=len(request.split()) > 20,  # Long request = complex
            risk_level=risk,
            complexity=Complexity.MODERATE,
            preferred_skill=skill,
            reasoning="Fallback analysis based on keywords",
            intent="unknown",
            confidence=0.5,
        )

    def requires_approval(self, strategy: Strategy) -> bool:
        """Check if this strategy requires user approval before execution."""
        return strategy.risk_level in (RiskLevel.MEDIUM, RiskLevel.HIGH)

    def requires_clarification(self, strategy: Strategy) -> bool:
        """Check if this strategy needs clarification from user."""
        return (
            len(strategy.clarification_questions) > 0
            or strategy.confidence < 0.6
        )
