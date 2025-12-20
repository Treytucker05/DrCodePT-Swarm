from __future__ import annotations

"""
Autonomous Agent Core - True agent architecture
Implements: Perception, Reasoning, Memory, Action, Feedback Loop
"""

import json
from typing import Any, Dict, List, Optional
from pathlib import Path


class AutonomousAgent:
    """
    Core autonomous agent with:
    - Perception: Observes environment and updates understanding
    - Reasoning: Generates and adapts plans based on state
    - Memory: Stores experiences and context
    - Action: Executes chosen actions dynamically
    - Feedback Loop: Continuously perceives → reasons → acts → reflects
    """
    
    def __init__(self, llm_client, domain: str = "general"):
        self.llm = llm_client
        self.domain = domain

        # MEMORY: Persistent state across interactions
        self.memory = {
            "conversation": [],  # Recent dialogue
            "actions_taken": [],  # History of actions and results
            "goals": [],  # User's stated goals
            "insights": {},  # Domain-specific learnings
            "context": {},  # Current environment state
            "mistakes": [],  # Failed actions and lessons learned
            "successes": [],  # Successful patterns to repeat
        }

        # Current state
        self.current_plan = []
        self.current_goal = None

        # Load persistent memory if available
        self._load_memory()
    
    def perceive(self, user_input: str, environment_state: Dict[str, Any], action_result: str = "") -> Dict[str, Any]:
        """
        PERCEPTION: Observe and understand current situation
        Returns: {perception, reasoning, plan, next_action, response}
        """
        raise NotImplementedError("Subclasses must implement perceive()")
    
    def act(self, action: Dict[str, Any]) -> str:
        """
        ACTION: Execute the decided action
        Returns: Result description
        """
        raise NotImplementedError("Subclasses must implement act()")
    
    def reflect(self, perception: str, action: Dict[str, Any], result: str):
        """
        FEEDBACK LOOP: Learn from what happened
        """
        action_type = action.get("type", "unknown")

        # Store action history
        self.memory["actions_taken"].append({
            "action": action,
            "result": result,
            "perception": perception,
        })

        # Learn from mistakes (failed actions)
        if result and any(word in result.lower() for word in ["failed", "error", "could not", "unable"]):
            lesson = {
                "action": action_type,
                "context": perception,
                "what_went_wrong": result,
                "timestamp": "now"
            }
            self.memory["mistakes"].append(lesson)
            print(f"[LEARNING] Recorded mistake: {action_type} failed")

        # Learn from successes
        elif result and action_type not in {"none", "ask_question"}:
            pattern = {
                "action": action_type,
                "context": perception,
                "outcome": result,
                "timestamp": "now"
            }
            self.memory["successes"].append(pattern)

        # Keep memory bounded
        if len(self.memory["actions_taken"]) > 20:
            self.memory["actions_taken"] = self.memory["actions_taken"][-20:]

        if len(self.memory["conversation"]) > 20:
            self.memory["conversation"] = self.memory["conversation"][-20:]

        if len(self.memory["mistakes"]) > 10:
            self.memory["mistakes"] = self.memory["mistakes"][-10:]

        if len(self.memory["successes"]) > 10:
            self.memory["successes"] = self.memory["successes"][-10:]

        # Persist memory after each reflection
        self._save_memory()
    
    def run(self, initial_input: str, environment_state: Dict[str, Any]):
        """
        Main agent loop: Perceive → Reason → Act → Reflect
        """
        print(f"\n[AGENT] Starting autonomous agent ({self.domain})...\n")
        
        # Initial perception
        decision = self.perceive(initial_input, environment_state)
        self._display_decision(decision)
        
        # Execute initial action
        action = decision.get("next_action", {})
        action_result = self.act(action)
        
        # Store in memory
        self.memory["conversation"].append({
            "user": initial_input,
            "agent": decision.get("response", "")
        })
        self.reflect(decision.get("perception", ""), action, action_result)
        
        # Conversation loop
        while True:
            try:
                user_input = input("\nYou: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n[AGENT] Goodbye!")
                return
            
            if not user_input:
                continue
            
            if user_input.lower() in {"exit", "quit", "done", "bye", "stop"}:
                print("[AGENT] Goodbye!")
                return
            
            # PERCEIVE: Understand new input with updated environment
            decision = self.perceive(user_input, environment_state, action_result)
            self._display_decision(decision)
            
            # ACT: Execute decided action
            action = decision.get("next_action", {})
            action_result = self.act(action)
            
            # REFLECT: Update memory
            self.memory["conversation"].append({
                "user": user_input,
                "agent": decision.get("response", "")
            })
            self.reflect(decision.get("perception", ""), action, action_result)
    
    def _display_decision(self, decision: Dict[str, Any]):
        """Display the agent's reasoning process"""
        print(f"[PERCEPTION] {decision.get('perception', '')}")
        print(f"[REASONING] {decision.get('reasoning', '')}")
        if decision.get('plan'):
            print(f"[PLAN] {' → '.join(decision.get('plan', []))}")
        print(f"\n[AGENT] {decision.get('response', '')}\n")

    def _load_memory(self):
        """Load persistent memory from disk"""
        memory_file = Path.home() / ".agent_memory" / f"{self.domain}_memory.json"
        if memory_file.exists():
            try:
                with open(memory_file, 'r') as f:
                    saved = json.load(f)
                    # Only load persistent parts (mistakes, successes, insights)
                    self.memory["mistakes"] = saved.get("mistakes", [])
                    self.memory["successes"] = saved.get("successes", [])
                    self.memory["insights"] = saved.get("insights", {})
                print(f"[MEMORY] Loaded {len(self.memory['mistakes'])} mistakes, {len(self.memory['successes'])} successes")
            except Exception as e:
                print(f"[MEMORY] Could not load memory: {e}")

    def _save_memory(self):
        """Save persistent memory to disk"""
        memory_dir = Path.home() / ".agent_memory"
        memory_dir.mkdir(exist_ok=True)
        memory_file = memory_dir / f"{self.domain}_memory.json"

        try:
            # Only save persistent parts
            to_save = {
                "mistakes": self.memory["mistakes"],
                "successes": self.memory["successes"],
                "insights": self.memory["insights"],
            }
            with open(memory_file, 'w') as f:
                json.dump(to_save, f, indent=2)
        except Exception as e:
            print(f"[MEMORY] Could not save memory: {e}")
