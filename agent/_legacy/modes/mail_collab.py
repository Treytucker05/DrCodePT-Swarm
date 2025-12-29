from __future__ import annotations

"""
Mail Collab Mode - Interactive mail organization with planning
Combines the collaborative planning approach with mail organization
"""

import os
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


def run_mail_collab(task: str) -> None:
    """
    Interactive mail organization with conversational planning.
    Uses LLM to understand user's goals and guide them through organization.
    """
    print(f"\n{CYAN}[MAIL COLLAB]{RESET} Let's work together to organize your mail.")
    print(f"{CYAN}[MAIL COLLAB]{RESET} I'll help you plan and execute your mail organization strategy.\n")
    
    from agent.llm import CodexCliClient, CodexCliNotFoundError, CodexCliAuthError
    from agent.modes.mail_supervised import run_mail_supervised
    
    try:
        client = CodexCliClient()
    except (CodexCliNotFoundError, CodexCliAuthError) as exc:
        print(f"{RED}[ERROR]{RESET} {exc}")
        print(f"{YELLOW}[FALLBACK]{RESET} Using standard mail mode instead...")
        run_mail_supervised(task)
        return
    
    system_prompt = """You are a helpful mail organization assistant. Your job is to:
1. Understand what the user wants to do with their mail
2. Ask clarifying questions to understand their goals
3. Suggest strategies for organizing folders, filtering spam, creating rules
4. Guide them through the process step by step

Be conversational and helpful. Ask questions to understand their needs.
Keep responses concise (2-3 sentences max unless explaining a strategy).

When the user is ready to take action, suggest they use the supervised mail mode.
"""

    conversation = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"I need help with: {task}"}
    ]
    
    response = client.chat(conversation, model="gpt-4o-mini", max_tokens=300)
    assistant_msg = response.get("content", "").strip()
    
    print(f"{CYAN}[ASSISTANT]{RESET} {assistant_msg}\n")
    conversation.append({"role": "assistant", "content": assistant_msg})
    
    while True:
        try:
            user_input = input(f"{GREEN}You:{RESET} ").strip()
        except KeyboardInterrupt:
            print(f"\n{YELLOW}[MAIL COLLAB]{RESET} Goodbye!")
            return
        
        if not user_input:
            continue
        
        lower = user_input.lower()
        if lower in {"exit", "quit", "done", "bye"}:
            print(f"{YELLOW}[MAIL COLLAB]{RESET} Goodbye!")
            return
        
        if lower in {"start", "begin", "let's do it", "ready", "go"}:
            print(f"\n{CYAN}[MAIL COLLAB]{RESET} Great! Launching supervised mail mode...\n")
            run_mail_supervised(task)
            return
        
        conversation.append({"role": "user", "content": user_input})
        
        response = client.chat(conversation, model="gpt-4o-mini", max_tokens=300)
        assistant_msg = response.get("content", "").strip()
        
        print(f"\n{CYAN}[ASSISTANT]{RESET} {assistant_msg}\n")
        conversation.append({"role": "assistant", "content": assistant_msg})
