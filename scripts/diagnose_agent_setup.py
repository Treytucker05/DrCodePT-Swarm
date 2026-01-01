"""
Diagnostic script to check agent setup and identify issues.

Usage:
    python scripts/diagnose_agent_setup.py
"""
from __future__ import annotations

import os
import sys
import subprocess
from pathlib import Path

# Add repo root to path for agent imports
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

def check_mark(ok: bool) -> str:
    # Use ASCII-safe characters for Windows console compatibility
    return f"{GREEN}[OK]{RESET}" if ok else f"{RED}[FAIL]{RESET}"

def print_header(text: str):
    print(f"\n{CYAN}{'='*60}{RESET}")
    print(f"{CYAN}{text:^60}{RESET}")
    print(f"{CYAN}{'='*60}{RESET}\n")

def check_python():
    """Check Python version and installation."""
    print_header("Python Environment")
    
    try:
        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"
        ok = version.major == 3 and version.minor >= 10
        print(f"{check_mark(ok)} Python {version_str}")
        if not ok:
            print(f"  {YELLOW}Warning: Python 3.10+ recommended{RESET}")
        return ok
    except Exception as e:
        print(f"{check_mark(False)} Python check failed: {e}")
        return False

def check_virtual_env():
    """Check if virtual environment is activated."""
    print_header("Virtual Environment")
    
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    venv_path = sys.prefix if in_venv else "Not activated"
    
    print(f"{check_mark(in_venv)} Virtual environment: {venv_path}")
    if not in_venv:
        print(f"  {YELLOW}Warning: Activate virtual environment with: .venv\\Scripts\\activate{RESET}")
    return in_venv

def check_dependencies():
    """Check if required packages are installed."""
    print_header("Dependencies")
    
    required_packages = [
        "pydantic",
        "requests",
        "colorama",
        "python-dotenv",
        "PyYAML",
    ]
    
    optional_packages = [
        "playwright",
        "pyautogui",
        "cryptography",
        "sentence-transformers",
        "faiss-cpu",
    ]
    
    all_ok = True
    
    print("Required packages:")
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"  {check_mark(True)} {package}")
        except ImportError:
            print(f"  {check_mark(False)} {package} - NOT INSTALLED")
            all_ok = False
    
    print("\nOptional packages:")
    for package in optional_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"  {check_mark(True)} {package}")
        except ImportError:
            print(f"  {YELLOW}[OPT]{RESET} {package} - Not installed (optional)")
    
    return all_ok

def check_codex_cli():
    """Check Codex CLI installation and authentication."""
    print_header("Codex CLI")
    
    # Check if codex command exists
    try:
        result = subprocess.run(
            ["codex", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"{check_mark(True)} Codex CLI installed: {version}")
        else:
            print(f"{check_mark(False)} Codex CLI command failed")
            return False
    except FileNotFoundError:
        print(f"{check_mark(False)} Codex CLI not found in PATH")
        print(f"  {YELLOW}Install Codex CLI and ensure it's in PATH{RESET}")
        return False
    except Exception as e:
        print(f"{check_mark(False)} Codex CLI check failed: {e}")
        return False
    
    # Check authentication
    try:
        result = subprocess.run(
            ["codex", "login", "status"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print(f"{check_mark(True)} Codex CLI authenticated")
            return True
        else:
            print(f"{check_mark(False)} Codex CLI not authenticated")
            print(f"  {YELLOW}Run: codex login{RESET}")
            return False
    except Exception as e:
        print(f"{check_mark(False)} Authentication check failed: {e}")
        return False

def check_env_file():
    """Check if .env file exists."""
    print_header("Configuration")
    
    repo_root = Path(__file__).resolve().parent.parent
    env_file = repo_root / ".env"
    
    exists = env_file.exists()
    print(f"{check_mark(exists)} .env file: {env_file}")
    
    if not exists:
        print(f"  {YELLOW}Create .env file with settings (see AGENT_SETUP_GUIDE.md){RESET}")
    
    return exists

def check_directory_structure():
    """Check if key directories exist."""
    print_header("Directory Structure")
    
    repo_root = Path(__file__).resolve().parent.parent
    
    required_dirs = [
        "agent",
        "agent/autonomous",
        "agent/modes",
        "agent/tools",
        "agent/llm",
    ]
    
    optional_dirs = [
        "runs",
        "agent/memory",
        "agent/playbooks",
    ]
    
    all_ok = True
    
    print("Required directories:")
    for dir_path in required_dirs:
        full_path = repo_root / dir_path
        exists = full_path.exists() and full_path.is_dir()
        print(f"  {check_mark(exists)} {dir_path}")
        if not exists:
            all_ok = False
    
    print("\nOptional directories (will be created automatically):")
    for dir_path in optional_dirs:
        full_path = repo_root / dir_path
        exists = full_path.exists() and full_path.is_dir()
        if exists:
            print(f"  {check_mark(True)} {dir_path}")
        else:
            print(f"  {YELLOW}[OPT]{RESET} {dir_path} - Will be created when needed")
    
    return all_ok

def check_agent_modules():
    """Check if key agent modules can be imported."""
    print_header("Agent Modules")
    
    modules_to_check = [
        ("agent.autonomous.runner", "AgentRunner"),
        ("agent.autonomous.config", "AgentConfig"),
        ("agent.llm.codex_cli_client", "CodexCliClient"),
        ("agent.autonomous.tools.registry", "ToolRegistry"),
    ]
    
    all_ok = True
    
    for module_path, class_name in modules_to_check:
        try:
            module = __import__(module_path, fromlist=[class_name])
            getattr(module, class_name)
            print(f"  {check_mark(True)} {module_path}.{class_name}")
        except Exception as e:
            print(f"  {check_mark(False)} {module_path}.{class_name} - {str(e)[:50]}")
            all_ok = False
    
    return all_ok

def run_simple_test():
    """Run a simple test to verify agent can start."""
    print_header("Simple Test")
    
    try:
        # Just try to import and create basic config
        from agent.autonomous.config import AgentConfig, RunnerConfig, PlannerConfig
        
        config = AgentConfig()
        runner_cfg = RunnerConfig(max_steps=5, timeout_seconds=60)
        planner_cfg = PlannerConfig(mode="react")
        
        print(f"  {check_mark(True)} Agent configuration can be created")
        return True
    except Exception as e:
        print(f"  {check_mark(False)} Agent configuration failed: {str(e)[:80]}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all diagnostic checks."""
    print(f"\n{CYAN}Autonomous Agent Setup Diagnostic{RESET}")
    print(f"{CYAN}{'='*60}{RESET}\n")
    
    results = []
    
    results.append(("Python", check_python()))
    results.append(("Virtual Environment", check_virtual_env()))
    results.append(("Dependencies", check_dependencies()))
    results.append(("Codex CLI", check_codex_cli()))
    results.append(("Configuration", check_env_file()))
    results.append(("Directory Structure", check_directory_structure()))
    results.append(("Agent Modules", check_agent_modules()))
    results.append(("Simple Test", run_simple_test()))
    
    # Summary
    print_header("Summary")
    
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    
    for name, ok in results:
        status = f"{GREEN}PASS{RESET}" if ok else f"{RED}FAIL{RESET}"
        print(f"  {status} {name}")
    
    print(f"\n{CYAN}{'='*60}{RESET}")
    print(f"Results: {passed}/{total} checks passed")
    
    if passed == total:
        print(f"{GREEN}✓ All checks passed! Agent should be ready to use.{RESET}\n")
        return 0
    else:
        print(f"{YELLOW}[WARN] Some checks failed. Review the output above and fix issues.{RESET}")
        print(f"{YELLOW}See AUTONOMOUS_AGENT_REPAIR_PLAN.md for detailed fix instructions.{RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())

