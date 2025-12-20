from agent.llm import CodexCliClient, schemas
from agent.llm.errors import CodexCliExecutionError
import json

llm = CodexCliClient.from_env()

# Simple prompt asking for JSON
prompt = """Analyze this request and return JSON.

USER: Show me my folders

Return JSON with:
- perception: "User wants to see folder list"
- reasoning: "Simple folder display request"
- next_action: {"type": "show_folders"}
- response: "Here are your folders"
"""

print("Testing Codex CLI...")
print(f"Prompt: {prompt[:100]}...")

try:
    result = llm.complete_json(prompt, schema_path=schemas.MAIL_AGENT)
    print(f"Success! Result: {json.dumps(result, indent=2)}")
except CodexCliExecutionError as e:
    print(f"CodexCliExecutionError:")
    print(f"Message: {e}")
    # Try to extract more details from the error message
    error_str = str(e)
    if "stdout:" in error_str:
        stdout_part = error_str.split("stdout:")[1].split("stderr:")[0] if "stderr:" in error_str else error_str.split("stdout:")[1]
        print(f"\nStdout: {stdout_part[:500]}")
    if "stderr:" in error_str:
        stderr_part = error_str.split("stderr:")[1]
        print(f"\nStderr (full): {stderr_part}")
except Exception as e:
    print(f"Other error: {type(e).__name__}: {e}")
