from __future__ import annotations

"""
Mail Agent - Autonomous agent specialized for email organization
"""

from typing import Any, Dict, List
from agent.core.autonomous_agent import AutonomousAgent

try:
    from colorama import Fore, Style
    CYAN, MAGENTA, GREEN, RED, YELLOW, RESET = (
        Fore.CYAN, Fore.MAGENTA, Fore.GREEN, Fore.RED, Fore.YELLOW, Style.RESET_ALL
    )
except Exception:
    CYAN = MAGENTA = GREEN = RED = YELLOW = RESET = ""


class MailAgent(AutonomousAgent):
    """Autonomous agent for mail organization"""
    
    def __init__(self, llm_client, yahoo_mail, folders: List[str], folder_counts: Dict[str, int]):
        super().__init__(llm_client, domain="mail")
        self.yahoo_mail = yahoo_mail
        self.folders = folders
        self.folder_counts = folder_counts
        
        self.memory["context"] = {
            "folders": folders,
            "folder_counts": folder_counts,
        }
    
    def perceive(self, user_input: str, environment_state: Dict[str, Any], action_result: str = "") -> Dict[str, Any]:
        """PERCEPTION: Understand mail organization request"""
        from agent.llm import schemas as llm_schemas
        import json

        recent_conv = self.memory["conversation"][-6:]
        recent_actions = self.memory["actions_taken"][-3:]
        mistakes = self.memory.get("mistakes", [])
        successes = self.memory.get("successes", [])

        prompt = f"""You are an autonomous mail organization agent. Analyze the situation and decide what to do.

ENVIRONMENT:
Folders: {', '.join(f"{f} ({self.folder_counts.get(f, 0)} msgs)" for f in self.folders[:10])}

MEMORY:
Recent conversation: {json.dumps(recent_conv, indent=2)}
Recent actions: {json.dumps(recent_actions, indent=2)}

LEARNED LESSONS (from past mistakes):
{json.dumps(mistakes, indent=2) if mistakes else "None yet"}

SUCCESSFUL PATTERNS (what worked before):
{json.dumps(successes, indent=2) if successes else "None yet"}

CURRENT INPUT:
User: {user_input}
{f"Last action result: {action_result}" if action_result else ""}

TASK: Perceive, reason, and decide.

1. PERCEPTION: What do you understand about the situation?
2. REASONING: What should you do and why? Consider past mistakes and successes.
3. PLAN: What steps will achieve the goal? (empty if just conversing)
4. NEXT ACTION:
   - ask_question: Need more information
   - scan_folder: See what's in a folder
   - create_folder: Create a new folder
   - show_folders: Show folder list
   - none: Just acknowledge/explain

5. RESPONSE: What to say (brief, conversational)

IMPORTANT:
- Listen to user intent. If they say "don't" or "not", respect that.
- Learn from past mistakes - don't repeat them.
- Use successful patterns when applicable."""

        try:
            result = self.llm.complete_json(prompt, schema_path=llm_schemas.MAIL_AGENT)
            return result
        except Exception as exc:
            return {
                "perception": f"Error: {exc}",
                "reasoning": "System error",
                "next_action": {"type": "none"},
                "response": "I'm having trouble processing that."
            }
    
    def act(self, action: Dict[str, Any]) -> str:
        """ACTION: Execute mail operations"""
        action_type = action.get("type")
        
        if action_type in {"ask_question", "none"}:
            return ""
        
        try:
            if action_type == "scan_folder":
                folder = action.get("folder", "INBOX")
                print(f"\n{CYAN}[ACTION]{RESET} Scanning {folder}...\n")
                
                headers = self.yahoo_mail.iter_headers(folder=folder, limit=100)
                senders = {}
                for h in headers:
                    sender = h.get("from", "")
                    if sender:
                        senders[sender] = senders.get(sender, 0) + 1
                
                top_senders = sorted(senders.items(), key=lambda x: x[1], reverse=True)[:10]
                
                result = f"Top senders in {folder}:\n"
                for sender, count in top_senders:
                    result += f"  - {sender}: {count} messages\n"
                
                print(result)
                return result
            
            elif action_type == "create_folder":
                folder = action.get("folder", "")
                if not folder:
                    return "No folder name specified"
                
                print(f"\n{CYAN}[ACTION]{RESET} Creating folder '{folder}'...\n")
                self.yahoo_mail.create_folder(folder)
                self.folders.append(folder)
                print(f"{GREEN}✓{RESET} Created: {folder}")
                return f"Created folder '{folder}'"
            
            elif action_type == "show_folders":
                print(f"\n{CYAN}[FOLDERS]{RESET}")
                for f in self.folders:
                    count = self.folder_counts.get(f, 0)
                    print(f"  - {f} ({count} messages)")
                print()
                return "Showed folder list"
        
        except Exception as exc:
            error_msg = f"Failed {action_type}: {exc}"
            print(f"{RED}[ERROR]{RESET} {error_msg}")
            return error_msg
        
        return ""
    
    def _display_decision(self, decision: Dict[str, Any]):
        """Display with colors"""
        print(f"{MAGENTA}[PERCEPTION]{RESET} {decision.get('perception', '')}")
        print(f"{MAGENTA}[REASONING]{RESET} {decision.get('reasoning', '')}")
        if decision.get('plan'):
            print(f"{MAGENTA}[PLAN]{RESET} {' → '.join(decision.get('plan', []))}")
        print(f"\n{CYAN}[AGENT]{RESET} {decision.get('response', '')}\n")


def run_mail_intelligent(task: str) -> None:
    """Run autonomous mail agent"""
    from agent.llm import CodexCliClient, CodexCliNotFoundError, CodexCliAuthError
    from agent.integrations import yahoo_mail
    
    try:
        client = CodexCliClient.from_env()
    except (CodexCliNotFoundError, CodexCliAuthError) as exc:
        print(f"{RED}[ERROR]{RESET} {exc}")
        return
    
    try:
        folders, delimiter = yahoo_mail.list_folders_with_delimiter()
        folder_counts = yahoo_mail.folder_counts(folders)
    except Exception as exc:
        print(f"{RED}[ERROR]{RESET} Failed to connect: {exc}")
        return
    
    agent = MailAgent(client, yahoo_mail, folders, folder_counts)
    agent.run(task, {"folders": folders, "folder_counts": folder_counts})
