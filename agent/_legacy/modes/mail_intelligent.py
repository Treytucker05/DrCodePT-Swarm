from __future__ import annotations

import json
import re
from typing import Dict, Any, List
from pathlib import Path

from agent.core.autonomous_agent import AutonomousAgent
from agent.llm.codex_cli_client import CodexCliClient
from agent.integrations import yahoo_mail
from agent.llm import schemas as llm_schemas


class MailAgent(AutonomousAgent):
    """
    Autonomous mail agent that uses Codex for reasoning (not execution).

    Uses two-stage approach:
    1. Reasoning: Plain codex with 'reason' profile (no execution)
    2. Action: Python code executed by the agent (not codex exec)
    """

    def __init__(self, llm_client, folders: List[str], folder_counts: Dict[str, int]):
        super().__init__(llm_client, domain="mail")
        self.folders = folders
        self.folder_counts = folder_counts
        self.memory["context"] = {
            "folders": folders,
            "folder_counts": folder_counts
        }

    def perceive(self, user_input: str, environment_state: Dict[str, Any], action_result: str = "") -> Dict[str, Any]:
        """
        Use LLM reasoning (codex --profile reason) to understand user intent and plan actions.
        This does NOT execute code - it only returns a JSON plan.
        """
        # Build context for LLM
        recent_conv = self.memory["conversation"][-3:] if self.memory["conversation"] else []
        recent_actions = self.memory["actions_taken"][-3:] if self.memory["actions_taken"] else []
        mistakes = self.memory["mistakes"][-2:] if self.memory["mistakes"] else []
        successes = self.memory["successes"][-2:] if self.memory["successes"] else []

        # Simplified folder list (top 10)
        folder_summary = "\n".join([
            f"- {f} ({self.folder_counts.get(f, 0)} emails)"
            for f in self.folders[:10]
        ])
        if len(self.folders) > 10:
            folder_summary += f"\n... and {len(self.folders) - 10} more folders"

        prompt = f"""You are a mail organization assistant. Analyze the user's request and decide what action to take.

AVAILABLE FOLDERS:
{folder_summary}

RECENT CONVERSATION:
{json.dumps(recent_conv, indent=2) if recent_conv else "None"}

PAST MISTAKES (learn from these):
{json.dumps(mistakes, indent=2) if mistakes else "None"}

SUCCESSFUL PATTERNS (repeat these):
{json.dumps(successes, indent=2) if successes else "None"}

USER REQUEST: {user_input}

{f"PREVIOUS ACTION RESULT: {action_result[:300]}" if action_result else ""}

AVAILABLE ACTIONS:
- scan_folder: Scan a specific folder (requires folder name)
- create_folder: Create a new folder (requires folder name)
- show_folders: Display all folders
- ask_question: Ask user for clarification
- none: No action needed

RULES:
- If user says "don't" or "not", respect that
- Learn from past mistakes
- Use successful patterns when applicable
- If unsure, ask for clarification

Return JSON with your analysis."""

        try:
            # Use reason_json (plain codex, no execution)
            result = self.llm.reason_json(prompt, schema_path=llm_schemas.MAIL_AGENT)
            return result
        except Exception as exc:
            # Fallback to simple response
            return {
                "perception": f"Error: {str(exc)[:100]}",
                "reasoning": "System error occurred",
                "plan": ["Show folders as fallback"],
                "next_action": {"type": "show_folders"},
                "response": "I encountered an error. Let me show you your folders."
            }

    def _fallback_perceive(self, user_input: str) -> Dict[str, Any]:
        """Fallback to rule-based perception if LLM reasoning fails."""
        user_lower = user_input.lower()

        if any(word in user_lower for word in ["show", "list", "display"]) and \
           any(word in user_lower for word in ["folder", "folders"]):
            return {
                "perception": "User wants to see folder list",
                "reasoning": "Detected 'show folders' pattern",
                "next_action": {"type": "show_folders"},
                "response": "Here are your mail folders:"
            }

        elif any(word in user_lower for word in ["scan", "check", "read"]):
            folder = self._extract_folder_name(user_input)
            if folder:
                return {
                    "perception": f"User wants to scan folder '{folder}'",
                    "reasoning": "Detected 'scan folder' pattern",
                    "next_action": {"type": "scan_folder", "folder": folder},
                    "response": f"Scanning folder '{folder}'..."
                }

        return {
            "perception": "Unclear request",
            "reasoning": "No matching pattern",
            "next_action": {"type": "ask_question", "question": "What would you like me to do?"},
            "response": "I can help you: show folders, scan a folder, or create a folder. What would you like?"
        }

    def _extract_folder_name(self, text: str, after_keywords: List[str] = None) -> str:
        """Extract folder name from user input using pattern matching."""
        if after_keywords is None:
            after_keywords = ["folder", "scan", "check", "read", "open"]

        # Try to find folder name after keywords
        for keyword in after_keywords:
            pattern = rf"{keyword}\s+['\"]?([A-Za-z0-9_\-\s]+)['\"]?"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                folder_name = match.group(1).strip()
                # Check if it's a valid folder name (exists in our list)
                for folder in self.folders:
                    if folder.lower() == folder_name.lower():
                        return folder
                # If not found, return the extracted name anyway
                return folder_name

        # Try to find quoted folder name
        quoted_match = re.search(r'["\']([^"\']+)["\']', text)
        if quoted_match:
            return quoted_match.group(1).strip()

        # Try to find INBOX, Sent, Trash, etc. (common folder names)
        common_folders = ["INBOX", "Sent", "Trash", "Drafts", "Spam", "Archive"]
        text_upper = text.upper()
        for folder in common_folders:
            if folder.upper() in text_upper:
                # Find the actual folder name in our list
                for actual_folder in self.folders:
                    if folder.upper() in actual_folder.upper():
                        return actual_folder

        return ""

    def act(self, action: Dict[str, Any]) -> str:
        """Execute mail-specific actions"""
        action_type = action.get("type", "none")

        if action_type == "scan_folder":
            folder = action.get("folder", "INBOX")
            try:
                emails = yahoo_mail.list_messages(limit=10, folder=folder)
                if not emails:
                    return f"Folder '{folder}' is empty or not found"

                summary = f"Found {len(emails)} emails in '{folder}':\n"
                for i, email in enumerate(emails[:5], 1):
                    summary += f"{i}. From: {email.get('from', 'Unknown')}, Subject: {email.get('subject', 'No subject')}\n"

                if len(emails) > 5:
                    summary += f"... and {len(emails) - 5} more"

                return summary
            except Exception as e:
                return f"Failed to scan folder '{folder}': {str(e)}"

        elif action_type == "create_folder":
            folder = action.get("folder")
            if not folder:
                return "Error: No folder name provided"

            try:
                yahoo_mail.create_folder(folder)
                self.folders.append(folder)
                return f"Successfully created folder '{folder}'"
            except Exception as e:
                return f"Failed to create folder '{folder}': {str(e)}"

        elif action_type == "show_folders":
            if not self.folders:
                return "No folders found"

            folder_list = "\n".join([
                f"- {f} ({self.folder_counts.get(f, 0)} emails)"
                for f in self.folders[:20]
            ])
            if len(self.folders) > 20:
                folder_list += f"\n... and {len(self.folders) - 20} more folders"

            return f"Available folders:\n{folder_list}"

        elif action_type == "ask_question":
            question = action.get("question", "What would you like me to do?")
            return f"Question: {question}"

        else:  # none or unknown
            return "No action taken"


def run_mail_intelligent(task: str) -> None:
    """
    Run the intelligent mail agent with LLM-based reasoning.

    Uses codex CLI with 'reason' profile for planning (no execution).
    """

    # Get initial folder state
    print("Loading mail folders...")
    folders = yahoo_mail.list_folders()
    folder_counts = yahoo_mail.folder_counts(folders[:10])

    # Create LLM client for reasoning
    llm_client = CodexCliClient.from_env()

    # Create agent
    agent = MailAgent(llm_client, folders, folder_counts)

    # Add user request to conversation
    agent.memory["conversation"].append({"role": "user", "content": task})

    print(f"\n{'='*60}")
    print(f"MAIL AGENT - Autonomous Mode (LLM-Based)")
    print(f"{'='*60}")
    print(f"Task: {task}\n")

    current_task = task

    # Main conversation loop
    while True:
        # Inner loop: up to 5 iterations per user input
        for iteration in range(5):
            print(f"\n--- Iteration {iteration + 1} ---")

            # Get previous action result
            action_result = agent.memory["actions_taken"][-1]["result"] if agent.memory["actions_taken"] else ""

            # Perceive
            decision = agent.perceive(current_task, {}, action_result)

            print(f"[PERCEPTION] {decision.get('perception', 'N/A')}")
            print(f"[REASONING] {decision.get('reasoning', 'N/A')}")
            print(f"[PLAN] {', '.join(decision.get('plan', []))}")
            print(f"[ACTION] {decision.get('next_action', {}).get('type', 'none')}")
            print(f"[RESPONSE] {decision.get('response', 'N/A')}")

            # Execute the action
            next_action = decision.get("next_action", {"type": "none"})
            result = agent.act(next_action)

            print(f"[RESULT] {result[:300]}")

            # Reflect on the outcome
            agent.reflect(
                perception=decision.get("perception", ""),
                action=next_action,
                result=result
            )

            # Add response to conversation
            agent.memory["conversation"].append({
                "role": "assistant",
                "content": decision.get("response", "")
            })

            # Check if we need user input
            if next_action.get("type") == "ask_question":
                print(f"\n{'='*60}")
                print(f"Waiting for user response...")
                print(f"{'='*60}")
                break

            # Check if task is complete
            if next_action.get("type") == "none":
                print(f"\n{'='*60}")
                print(f"Task completed")
                print(f"{'='*60}")
                return

        # Wait for user input
        try:
            user_response = input("\n> ").strip()
            if not user_response:
                continue

            # Check for exit commands
            if user_response.lower() in {"exit", "quit", "done", "bye"}:
                print("Exiting mail agent.")
                return

            # Add user response to conversation
            agent.memory["conversation"].append({
                "role": "user",
                "content": user_response
            })

            # Update current task with user response
            current_task = user_response

        except (EOFError, KeyboardInterrupt):
            print("\nExiting mail agent.")
            return
