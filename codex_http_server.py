"""
Minimal Codex HTTP wrapper.

Endpoints:
  POST /codex/run
    body: { "prompt": "...", "metadata": {...optional...} }
    returns: echo of prompt plus a placeholder result.

This is intentionally lightweight so Zapier MCP can call *something* reliable today.
If you have a real Codex API, replace the placeholder section with your API call or
CLI invocation, keeping the same response shape.
"""

from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Any, Dict
import datetime
import uuid

app = FastAPI(title="Codex HTTP Wrapper", version="0.1.0")


class RunRequest(BaseModel):
    prompt: str = Field(..., description="User prompt or task for Codex")
    metadata: Dict[str, Any] | None = Field(
        default=None, description="Optional extra fields passed through"
    )


@app.post("/codex/run")
async def codex_run(req: RunRequest):
    """
    Placeholder implementation:
    - Generates a request id
    - Echoes the prompt
    - Returns a canned 'acknowledged' status

    Swap the body of this function with your real Codex call and return its output.
    """
    request_id = str(uuid.uuid4())
    now = datetime.datetime.utcnow().isoformat() + "Z"

    # TODO: integrate your actual Codex call here. Example pseudocode:
    # result = real_codex_client.run(prompt=req.prompt, metadata=req.metadata)
    # return {"request_id": request_id, "timestamp": now, "result": result}

    return {
        "request_id": request_id,
        "timestamp": now,
        "status": "acknowledged",
        "echo": {"prompt": req.prompt, "metadata": req.metadata},
        "note": "Replace placeholder logic in codex_run with your real Codex call.",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
