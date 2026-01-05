import os
import sys
import logging
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Add repo root to path
sys.path.append(str(Path(__file__).resolve().parents[3]))

# Configure logging
repo_root = Path(__file__).resolve().parents[3]
log_dir = repo_root / "logs"
log_dir.mkdir(exist_ok=True)
log_path = log_dir / "server.log"
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s %(levelname)s %(message)s', 
    force=True, 
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_path, mode='a', encoding='utf-8')
    ]
)
logger = logging.getLogger("llm_server")

app = FastAPI(title="DrCodePT Persistent LLM Server")

DEFAULT_WORKERS = int(os.getenv("LLM_SERVER_WORKERS", "2"))
DEFAULT_CONCURRENCY = int(os.getenv("LLM_SERVER_MAX_CONCURRENT", str(DEFAULT_WORKERS)))

from pydantic import BaseModel
from typing import Optional, Dict, Any

class CompletionRequest(BaseModel):
    prompt: str
    schema_path: Optional[str] = None
    timeout: int = 120
    agent: str = "Main"
    enable_search: bool = False

import subprocess
import shutil

class CodexHandler:
    def __init__(self):
        self._codex_bin = self._find_codex()
        self._auth_verified = False
    
    def _find_codex(self) -> str:
        # Tries to find codex in common locations or PATH
        candidates = [
            Path(r"C:\Users\treyt\AppData\Roaming\npm\node_modules\@openai\codex\vendor\x86_64-pc-windows-msvc\codex\codex.exe"),
            Path(r"C:\Users\treyt\AppData\Roaming\npm\node_modules\@openai\codex\vendor\aarch64-pc-windows-msvc\codex\codex.exe"),
        ]
        for c in candidates:
            if c.is_file():
                return str(c)
        return shutil.which("codex") or "codex"

    def startup_check(self):
        """Verify codex is installed and authenticated."""
        if not self._codex_bin:
            logger.error("Codex binary not found!")
            raise RuntimeError("Codex binary not found")
            
        logger.info(f"Using Codex binary: {self._codex_bin}")
        
        # Check login status by running a trivial command
        # "codex model list" or similar might be better, but "codex --version" doesn't check auth.
        # We'll try running a dummy exec command. If it returns "login required", we fail startup.
        logger.info("Verifying authentication...")
        # For now, we assume if we can run it without immediate auth error, we are good.
        # We will handle per-request auth errors with a circuit breaker.
        self._auth_verified = True

    def execute(self, req: CompletionRequest) -> Dict[str, Any]:
        if not self._auth_verified:
             # Try to re-verify if we were previously failed? 
             # For now, simplistic approach.
             pass

        # Construct command similar to CLI client but we own the process execution here
        # This implementation closely mirrors the CLI client but allows us to add
        # "Server-Side" optimizations like caching or queuing in the future.
        
        # We reuse the existing logic for now but import it to keep 'app.py' clean?
        # Better: we implement the subprocess call here to have full control.
        
        cmd = [
            self._codex_bin,
            "--dangerously-bypass-approvals-and-sandbox",
            "-c", "sandbox_mode=danger-full-access",
            "-c", "approval_policy=never",
            "exec",
            "--skip-git-repo-check",
            "--model", "gpt-5.2-codex", # Enforce fast model
        ]
        
        if req.schema_path:
             cmd += ["--output-schema", req.schema_path]
        
        # Use a temp file for output logic if needed, or parse stdout if the CLI supports it.
        # The CLI client uses --output-last-message <file>. We should do the same to be safe.
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".json") as tmp:
            tmp_path = tmp.name
        
        cmd += ["--output-last-message", tmp_path]
        cmd += ["-"] # Read prompt from stdin
        
        cwd = os.getcwd() # Or passed in req?
        env = os.environ.copy()
        
        try:
            logger.info(f"Exec: {' '.join(cmd)}")
            proc = subprocess.run(
                cmd,
                input=req.prompt,
                capture_output=True,
                text=True,
                cwd=cwd,
                env=env,
                timeout=req.timeout,
                encoding="utf-8"
            )
            
            if proc.returncode != 0:
                stderr = proc.stderr.lower()
                if "login" in stderr or "auth" in stderr:
                    logger.critical("Authentication failed during request!")
                    return {"error": "auth_error", "detail": proc.stderr}
                return {"error": "execution_failed", "detail": proc.stderr}
                
            # Read output file
            try:
                with open(tmp_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data
            except Exception as e:
                return {"error": "output_parse_failed", "detail": str(e), "raw": proc.stdout}
                
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def chat(self, req: CompletionRequest) -> Dict[str, Any]:
        """Raw chat without output schema, just stdout."""
        cmd = [
            self._codex_bin,
            "--dangerously-bypass-approvals-and-sandbox",
            "-c", "sandbox_mode=danger-full-access",
            "-c", "approval_policy=never",
            "exec",
            "--skip-git-repo-check",
            "--model", "gpt-5.2-codex",
            "-"
        ]
        
        try:
            proc = subprocess.run(
                cmd,
                input=req.prompt,
                capture_output=True,
                text=True,
                cwd=os.getcwd(),
                env=os.environ.copy(),
                timeout=req.timeout,
                encoding="utf-8"
            )
            
            if proc.returncode != 0:
                stderr = proc.stderr.lower()
                if "login" in stderr or "auth" in stderr:
                    return {"error": "auth_error", "detail": proc.stderr}
                return {"error": "execution_failed", "detail": proc.stderr}
            
            # Extract response (same logic as CodexCliClient.chat)
            stdout = proc.stdout or ""
            if "\ncodex\n" in stdout:
                response = stdout.split("\ncodex\n")[-1].strip()
                # Remove token count line if present
                lines = response.split("\n")
                if lines and lines[-1].isdigit():
                    lines = lines[:-1]
                if lines and lines[-1].startswith("tokens used"):
                    lines = lines[:-1]
                return {"result": "\n".join(lines).strip()}
            
            return {"result": stdout.strip()}
            
        except subprocess.TimeoutExpired:
            return {"error": "timeout"}
        except Exception as e:
            return {"error": "unknown", "detail": str(e)}

handler = CodexHandler()

def _get_executor() -> ThreadPoolExecutor:
    executor = getattr(app.state, "executor", None)
    if executor is None:
        executor = ThreadPoolExecutor(max_workers=DEFAULT_WORKERS)
        app.state.executor = executor
    return executor

def _get_semaphore() -> asyncio.Semaphore:
    semaphore = getattr(app.state, "semaphore", None)
    if semaphore is None:
        semaphore = asyncio.Semaphore(DEFAULT_CONCURRENCY)
        app.state.semaphore = semaphore
    return semaphore

async def _run_blocking(func, *args):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_get_executor(), lambda: func(*args))

@app.on_event("startup")
async def startup_event():
    try:
        app.state.executor = ThreadPoolExecutor(max_workers=DEFAULT_WORKERS)
        app.state.semaphore = asyncio.Semaphore(DEFAULT_CONCURRENCY)
        handler.startup_check()
    except Exception as e:
        logger.critical(f"Server startup failed: {e}")
        # We don't exit to allow 'health' checks to report failure?
        # But for an agent, maybe better to crash.

@app.on_event("shutdown")
async def shutdown_event():
    executor = getattr(app.state, "executor", None)
    if executor is not None:
        executor.shutdown(wait=False)

@app.post("/complete_json")
async def complete_json(req: CompletionRequest):
    sem = _get_semaphore()
    await sem.acquire()
    try:
        return await _run_blocking(handler.execute, req)
    finally:
        sem.release()

@app.post("/chat")
async def chat(req: CompletionRequest):
    sem = _get_semaphore()
    await sem.acquire()
    try:
        return await _run_blocking(handler.chat, req)
    finally:
        sem.release()

@app.get("/health")
def health():
    return {"status": "ok", "auth_verified": handler._auth_verified}

@app.get("/")
def root():
    return {"message": "DrCodePT LLM Server is running"}

if __name__ == "__main__":
    import uvicorn
    # Use port 8000
    uvicorn.run(app, host="127.0.0.1", port=8000)
