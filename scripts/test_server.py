
import sys
from pathlib import Path

# Add repo root to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

try:
    from agent.llm.server_client import ServerClient
except ImportError:
    print("Could not import ServerClient")
    sys.exit(1)

def test_connectivity():
    client = ServerClient.from_env()
    # Manual health check since we didn't add a health method to ServerClient yet,
    # but let's try a simple completion call that should fail if server is down
    # or succeed if up.
    
    print("Testing connection...")
    try:
        import requests
        resp = requests.get("http://127.0.0.1:8000/health")
        print(f"Health Check: {resp.status_code} {resp.json()}")
    except Exception as e:
        print(f"Health Check Failed: {e}")
        return

    print("Testing completion...")
    res = client.complete_json(
        prompt="Test",
        schema_path=Path("test_schema.json"), # Dummy path
        timeout_seconds=5
    )
    print(f"Completion Result: {res}")

if __name__ == "__main__":
    test_connectivity()
