from __future__ import annotations

import json
import re
from typing import Dict, Any, List
from pathlib import Path

from agent.core.autonomous_agent import AutonomousAgent
from agent.tools.yahoo_mail import YahooMail


class MailAgent(AutonomousAgent):
    """
    Autonomous mail agent that uses rule-based reasoning for simple operations.

    This agent does NOT use codex exec for reasoning (that's an execution mode).
    Instead, it uses pattern matching and rules to understand user intent.
    """

    def __init__(self, llm_client, yahoo_mail, folders: List[str], folder_counts: Dict[str, int]):
        super().__init__(llm_client, domain="mail")
        self.yahoo_mail = yahoo_mail
        self.folders = folders
        self.folder_counts = folder_counts
        self.memory["context"] = {
            "folders": folders,
            "folder_counts": folder_counts
        }

    def perceive(self, user_input: str, environment_state: Dict[str, Any], action_result: str = "") -> Dict[str, Any]:
        """
        Rule-based perception: analyze user input using pattern matching.
        No LLM needed for simple mail operations.
        """
        user_lower = user_input.lower()

        # Pattern matching for common intents
        if any(word in user_lower for word in ["show", "list", "display", "see"]) and \
           any(word in user_lower for word in ["folder", "folders"]):
            return {
                "perception": "User wants to see folder list",
                "reasoning": "Detected 'show/list folders' pattern",
                "plan": ["Display all folders with counts"],
                "next_action": {"type": "show_folders"},
                "response": "Here are your mail folders:"
            }

        elif any(word in user_lower for word in ["scan", "check", "read", "open"]):
            # Extract folder name
            folder = self._extract_folder_name(user_input)
            if folder:
                return {
                    "perception": f"User wants to scan folder '{folder}'",
                    "reasoning": f"Detected 'scan folder' pattern with folder name '{folder}'",
                    "plan": [f"Scan folder '{folder}'", "Display email summary"],
                    "next_action": {"type": "scan_folder", "folder": folder},
                    "response": f"Scanning folder '{folder}'..."
                }
            else:
                return {
                    "perception": "User wants to scan a folder but didn't specify which",
                    "reasoning": "Detected 'scan' intent but no folder name",
                    "plan": ["Ask user which folder to scan"],
                    "next_action": {"type": "ask_question", "question": "Which folder would you like to scan?"},
                    "response": "Which folder would you like to scan?"
                }

        elif any(word in user_lower for word in ["create", "make", "add", "new"]) and \
             any(word in user_lower for word in ["folder"]):
            # Extract folder name
            folder = self._extract_folder_name(user_input, after_keywords=["folder", "called", "named"])
            if folder:
                return {
                    "perception": f"User wants to create folder '{folder}'",
                    "reasoning": f"Detected 'create folder' pattern with name '{folder}'",
                    "plan": [f"Create folder '{folder}'", "Confirm creation"],
                    "next_action": {"type": "create_folder", "folder": folder},
                    "response": f"Creating folder '{folder}'..."
                }
            else:
                return {
                    "perception": "User wants to create a folder but didn't specify name",
                    "reasoning": "Detected 'create folder' intent but no name",
                    "plan": ["Ask user for folder name"],
                    "next_action": {"type": "ask_question", "question": "What would you like to name the folder?"},
                    "response": "What would you like to name the new folder?"
                }

        elif any(word in user_lower for word in ["organize", "sort", "clean", "manage"]):
            return {
                "perception": "User wants to organize mail",
                "reasoning": "Detected 'organize' intent - complex operation",
                "plan": ["Show folders first", "Ask for organization strategy"],
                "next_action": {"type": "show_folders"},
                "response": "Let me show you your folders first, then we can discuss how to organize your mail."
            }

        else:
            # Unknown intent
            return {
                "perception": f"Unclear request: '{user_input[:50]}'",
                "reasoning": "No matching pattern found",
                "plan": ["Ask for clarification"],
                "next_action": {"type": "ask_question", "question": "I can help you: show folders, scan a folder, or create a folder. What would you like?"},
                "response": "I can help you with:\n- Show folders\n- Scan a folder\n- Create a folder\n\nWhat would you like to do?"
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
                emails = self.yahoo_mail.scan_folder(folder)
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
                self.yahoo_mail.create_folder(folder)
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
    Run the intelligent mail agent with rule-based reasoning.

    This version does NOT use codex exec for reasoning (that's an execution mode).
    Instead, it uses pattern matching to understand user intent.
    """

    # Initialize Yahoo Mail
    yahoo_mail = YahooMail()

    # Get initial folder state
    print("Loading mail folders...")
    folders = yahoo_mail.list_folders()
    folder_counts = {f: yahoo_mail.get_folder_count(f) for f in folders[:10]}

    # Create agent (llm_client is None since we're not using LLM for reasoning)
    agent = MailAgent(None, yahoo_mail, folders, folder_counts)

    # Add user request to conversation
    agent.memory["conversation"].append({"role": "user", "content": task})

    print(f"\n{'='*60}")
    print(f"MAIL AGENT - Autonomous Mode (Rule-Based)")
    print(f"{'='*60}")
    print(f"Task: {task}\n")

    # Main loop: up to 5 iterations
    for iteration in range(5):
        print(f"\n--- Iteration {iteration + 1} ---")

        # Get previous action result
        action_result = agent.memory["actions_taken"][-1]["result"] if agent.memory["actions_taken"] else ""

        # Perceive (rule-based, no LLM)
        decision = agent.perceive(task, {}, action_result)

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

        # Check if we're done
        if next_action.get("type") in {"none", "ask_question"}:
            print(f"\n{'='*60}")
            print(f"Agent completed task")
            print(f"{'='*60}")
            break

    print(f"\nFinal response: {decision.get('response', 'Task completed')}")
