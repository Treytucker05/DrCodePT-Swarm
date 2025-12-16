from __future__ import annotations

"""
Recorder: Watch user browser actions and generate playbooks/tasks.

Usage:
    python -m agent.recorder --site blackboard --output memory/site_playbooks/blackboard.yaml
"""

import asyncio
import json
import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

import yaml

ROOT = Path(__file__).resolve().parent


class ActionRecorder:
    def __init__(self, site_name: str):
        self.site_name = site_name
        self.actions: List[Dict[str, Any]] = []
        self.start_url = ""
        self.selectors_used: List[str] = []
        self.forms_found: List[str] = []

    async def start_recording(self, start_url: str = ""):
        """Launch browser and record user actions."""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            print("ERROR: Playwright not installed. Run: pip install playwright && playwright install")
            return

        print(f"\n{'='*50}")
        print(f"  RECORDING SESSION: {self.site_name}")
        print(f"{'='*50}")
        print("\nA browser will open. Perform your actions.")
        print("When done, close the browser window.\n")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()

            # Track navigation
            def on_request(request):
                if request.resource_type == "document":
                    self.actions.append({
                        "type": "navigation",
                        "url": request.url,
                        "timestamp": datetime.now().isoformat()
                    })
                    print(f"  NAV: {request.url[:80]}")

            page.on("request", on_request)

            # Inject action tracking script
            tracking_script = """
                window.__recordedActions = window.__recordedActions || [];
                
                document.addEventListener('click', (e) => {
                    const target = e.target;
                    let selector = '';
                    if (target.id) selector = '#' + target.id;
                    else if (target.name) selector = '[name="' + target.name + '"]';
                    else if (target.className && typeof target.className === 'string') 
                        selector = '.' + target.className.split(' ')[0];
                    else selector = target.tagName.toLowerCase();
                    
                    window.__recordedActions.push({
                        type: 'click',
                        selector: selector,
                        tag: target.tagName,
                        text: (target.innerText || '').substring(0, 50),
                        timestamp: new Date().toISOString()
                    });
                }, true);

                document.addEventListener('input', (e) => {
                    const target = e.target;
                    let selector = '';
                    if (target.id) selector = '#' + target.id;
                    else if (target.name) selector = '[name="' + target.name + '"]';
                    else if (target.className && typeof target.className === 'string')
                        selector = '.' + target.className.split(' ')[0];
                    else selector = target.tagName.toLowerCase();
                    
                    window.__recordedActions.push({
                        type: 'input',
                        selector: selector,
                        inputType: target.type || 'text',
                        name: target.name || '',
                        timestamp: new Date().toISOString()
                    });
                }, true);

                document.addEventListener('submit', (e) => {
                    window.__recordedActions.push({
                        type: 'submit',
                        formId: e.target.id || '',
                        timestamp: new Date().toISOString()
                    });
                }, true);
            """
            
            await page.add_init_script(tracking_script)

            # Navigate to starting point
            if start_url:
                self.start_url = start_url
            else:
                self.start_url = input("Enter starting URL (or press Enter for blank tab): ").strip()
            
            if self.start_url:
                try:
                    await page.goto(self.start_url, wait_until="domcontentloaded", timeout=30000)
                except Exception as e:
                    print(f"Warning: Initial navigation issue: {e}")
            
            print("\nRecording... Close the browser window when done.\n")

            # Wait for browser to close
            try:
                while True:
                    # Check if browser is still open
                    try:
                        pages = context.pages
                        if len(pages) == 0:
                            break
                    except:
                        break
                    
                    # Collect actions from page
                    try:
                        js_actions = await page.evaluate("window.__recordedActions || []")
                        for action in js_actions:
                            action_key = f"{action['type']}_{action.get('selector', '')}_{action.get('timestamp', '')}"
                            existing_keys = [f"{a['type']}_{a.get('selector', '')}_{a.get('timestamp', '')}" for a in self.actions]
                            if action_key not in existing_keys:
                                self.actions.append(action)
                                print(f"  {action['type'].upper()}: {action.get('selector', '')[:50]}")
                        await page.evaluate("window.__recordedActions = []")
                    except:
                        pass
                    
                    await asyncio.sleep(0.5)
                    
            except KeyboardInterrupt:
                print("\nStopping recording...")

            # Final action collection
            try:
                js_actions = await page.evaluate("window.__recordedActions || []")
                self.actions.extend(js_actions)
            except:
                pass

            # Save storage state
            sessions_dir = ROOT / "sessions"
            sessions_dir.mkdir(exist_ok=True)
            state_path = sessions_dir / f"{self.site_name}_state.json"
            try:
                await context.storage_state(path=str(state_path))
                print(f"\nSession state saved to: {state_path}")
            except Exception as e:
                print(f"Warning: Could not save session state: {e}")

            try:
                await browser.close()
            except:
                pass

        print(f"\nRecorded {len(self.actions)} actions total.")

    def generate_playbook(self) -> Dict[str, Any]:
        """Generate a site playbook from recorded actions."""
        
        # Extract unique selectors
        click_selectors = list(set([
            a["selector"] for a in self.actions 
            if a.get("type") == "click" and a.get("selector") and a["selector"] != "undefined"
        ]))
        input_selectors = list(set([
            a["selector"] for a in self.actions 
            if a.get("type") == "input" and a.get("selector") and a["selector"] != "undefined"
        ]))
        
        # Build login flow from actions
        login_flow = []
        for action in self.actions:
            if action.get("type") == "input" and action.get("selector"):
                login_flow.append({
                    "selector": action["selector"],
                    "action": "fill",
                    "field_type": action.get("inputType", "text")
                })
            elif action.get("type") == "click":
                text = action.get("text", "").lower()
                selector = action.get("selector", "")
                if any(kw in text for kw in ["login", "submit", "sign in", "log in"]) or \
                   any(kw in selector.lower() for kw in ["login", "submit", "signin"]):
                    login_flow.append({
                        "selector": selector,
                        "action": "click",
                        "note": action.get("text", "")[:30]
                    })
            elif action.get("type") == "submit":
                login_flow.append({"action": "submit"})

        # Extract navigation URLs
        nav_urls = list(set([
            a["url"] for a in self.actions 
            if a.get("type") == "navigation" and a.get("url")
        ]))

        playbook = {
            "site": self.site_name,
            "start_url": self.start_url or (nav_urls[0] if nav_urls else ""),
            "recorded_at": datetime.now().isoformat(),
            "action_count": len(self.actions),
            "login_flow": login_flow[:15],
            "known_urls": nav_urls[:30],
            "working_selectors": {
                "clickable": click_selectors[:40],
                "inputs": input_selectors[:30]
            },
            "known_quirks": [
                "Auto-generated - review and update as needed"
            ],
            "notes": f"Recorded {len(self.actions)} actions on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        }

        return playbook

    def generate_task(self, task_id: str, goal: str) -> Dict[str, Any]:
        """Generate a task YAML from recording."""
        
        task = {
            "id": task_id,
            "name": f"Recorded task for {self.site_name}",
            "type": "browser",
            "goal": goal,
            "inputs": {},
            "output": {
                "destination": f"outputs/{task_id}_result.json",
                "format": "json"
            },
            "definition_of_done": f"Successfully completed: {goal}",
            "verify": [
                {"id": "file_exists", "args": {"path": f"outputs/{task_id}_result.json"}}
            ],
            "allowed_paths": ["outputs/", "sessions/"],
            "tools_allowed": ["browser"],
            "stop_rules": {
                "max_attempts": 3,
                "max_minutes": 10,
                "max_tool_calls": 50
            },
            "on_fail": "escalate",
            "url": self.start_url,
            "session_state_path": f"sessions/{self.site_name}_state.json"
        }

        return task

    def save_playbook(self, output_path: str) -> Path:
        """Save playbook to YAML file."""
        playbook = self.generate_playbook()
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(playbook, sort_keys=False, allow_unicode=True), encoding="utf-8")
        print(f"Playbook saved to: {path}")
        return path

    def save_task(self, output_path: str, task_id: str, goal: str) -> Path:
        """Save task to YAML file."""
        task = self.generate_task(task_id, goal)
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(task, sort_keys=False, allow_unicode=True), encoding="utf-8")
        print(f"Task saved to: {path}")
        return path


def run_recorder(site: str, start_url: str = "", playbook_output: str = None, task_output: str = None, task_id: str = None, goal: str = None):
    """Run the recorder programmatically."""
    recorder = ActionRecorder(site)
    asyncio.run(recorder.start_recording(start_url))
    
    # Default playbook path
    if playbook_output is None:
        playbook_output = str(ROOT / "memory" / "site_playbooks" / f"{site}.yaml")
    
    recorder.save_playbook(playbook_output)
    
    if task_output:
        tid = task_id or f"recorded_{site}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        g = goal or f"Complete recorded workflow for {site}"
        recorder.save_task(task_output, tid, g)


async def main():
    parser = argparse.ArgumentParser(description="Record browser actions and generate playbooks")
    parser.add_argument("--site", required=True, help="Site name (e.g., blackboard, google)")
    parser.add_argument("--url", default="", help="Starting URL")
    parser.add_argument("--playbook", help="Output path for playbook YAML")
    parser.add_argument("--task", help="Output path for task YAML")
    parser.add_argument("--task-id", help="Task ID for generated task")
    parser.add_argument("--goal", help="Goal description for generated task")
    
    args = parser.parse_args()

    recorder = ActionRecorder(args.site)
    await recorder.start_recording(args.url)

    # Default output paths
    playbook_path = args.playbook or str(ROOT / "memory" / "site_playbooks" / f"{args.site}.yaml")
    recorder.save_playbook(playbook_path)

    if args.task:
        task_id = args.task_id or f"recorded_{args.site}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        goal = args.goal or f"Complete recorded workflow for {args.site}"
        recorder.save_task(args.task, task_id, goal)


if __name__ == "__main__":
    asyncio.run(main())
