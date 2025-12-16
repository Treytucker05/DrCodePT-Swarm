# Dependency Checklist

## Python / MCP Stack
| Component | File | Status | Notes |
| --- | --- | --- | --- |
| fastmcp>=0.1.0 | `PROGRAMS/fastmcp-server/requirements.txt` | ✅ Installed previously (venv exists) | Needed for FastMCP app + CLI tooling |
| pandas, scikit-learn | same | ⚠️ Assume installed, but re-run `pip install -r requirements.txt` inside venv before redeploy | Heavy dependencies; verify wheel cache to avoid install delays |
| pypdf, python-pptx | same | ✅ Verified versions support slide/text extraction | Required for module ingestion |
| watchdog | same | ⚠️ Optional but useful for hot reload; ensure Windows permissions allow file watching |

## Node / Dashboard Stack
| Component | File | Status | Notes |
| --- | --- | --- | --- |
| express, cors, dotenv, joi, axios, pino | `IN_DEVELOPMENT/dashboard-api/package.json` | ✅ npm install completed previously (node_modules present) | Needed for REST API + validation + logging |
| jest | devDependency | ⚠️ Tests exist but not run tonight; execute `npm test` before shipping HALF B | Confidence boost for API contracts |

## External Services
| Service | Status | Notes |
| --- | --- | --- |
| Anki Desktop + AnkiConnect | ❌ Not running (port 8765 offline). Need to launch Anki and confirm add-on installed. |
| AnkiWeb | ⚠️ Credentials documented but not loaded into `.env`; confirm login still works. |
| ngrok | ✅ Config file present (token stored), but CLI must run manually when exposing StudyMCP. Document version used. |
| OneDrive Sync | ✅ PT School folders synced; ensure StudyMCP writes do not conflict with OneDrive locks (consider local cache if conflicts appear). |

## Filesystem / Permissions
- `C:\Users\treyt\OneDrive\Desktop\PT School\` – read/write confirmed (deck creation already works). Use atomic writes (`tempfile` + rename) when multiple systems mutate decks.
- `_decks-index.json` is regenerated per course; ensure newline handling remains Windows-friendly (UTF-8 w/o BOM).

## Actions Before HALF B Coding
1. Activate `PROGRAMS/fastmcp-server/venv` and run `python -m pip install -r requirements.txt` to guarantee parity with the version ChatGPT already uses.
2. From `IN_DEVELOPMENT/dashboard-api`, run `npm install` (if node_modules missing) and `npm test` to confirm the API still passes its suite before we rely on it for monitoring card counts.
3. Launch Anki desktop → verify `Tools > Add-ons > AnkiConnect` is enabled → hit `http://127.0.0.1:8765` manually to record expected JSON response.
4. Store all secrets (`ANKI_EMAIL`, `ANKI_PASSWORD`, `NGROK_AUTHTOKEN`) inside a `.env` that is excluded by `.gitignore`, then load them via `python-dotenv` inside StudyMCP.
