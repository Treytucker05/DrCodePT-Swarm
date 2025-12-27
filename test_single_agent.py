import sys
from pathlib import Path

sys.path.insert(0, r"C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm")

from agent.llm.codex_cli_client import CodexCliClient

client = CodexCliClient(profile_reason="fast")

prompt = "Return JSON: {\"test\": \"hello\", \"status\": \"working\"}"

print("[TEST] Calling Codex with simple prompt...")
result = client.reason_json(
    prompt,
    schema_path=Path("agent/llm/schemas/chat_response.schema.json"),
    timeout_seconds=60,
)

print(f"[TEST] Result: {result}")
