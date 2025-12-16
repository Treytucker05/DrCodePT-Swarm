# Workspace Overview (DrCodePT-Swarm)

## Quick start
- Start Magg MCP hub:  `C:\Users\treyt\AppData\Roaming\Python\Python314\Scripts\magg.exe serve --config .magg\config.json`
- Start Codex normally; it will auto-run Magg with the same config (set in `~/.codex/config.toml`).
- See MCP status: `magg server list`

## Key folders
- .magg/               – Magg config + cloned MCP server repos (mailnet) and runtime data.
- CODEX/               – How Codex is wired to Magg (`CODEX/README.txt`).
- MCP/                 – MCP server status, commands, required envs (`MCP/README.txt`).
- DOCS/, PROGRAMS/, Codex Tasks/, etc. – original project folders (unchanged).

## MCP servers registered (prefix)
- fetch   – web fetch -> markdown (enabled)
- files   – filesystem over repo root (enabled)
- toolz   – mcp-toolz: context/todo persistence + cross-LLM feedback (enabled)
- airflow – Airflow REST tools (enabled; set creds)
- pinecone – Pinecone server (enabled; set API key)
- mailnet – Gmail/Outlook agentic email (disabled until creds set)

## Credentials to set before heavy use
- Pinecone: set `PINECONE_API_KEY` (and region if needed) before starting Magg.
- Airflow: set `AIRFLOW_BASE_URL` + auth (`AIRFLOW_USERNAME`/`AIRFLOW_PASSWORD` or `AIRFLOW_TOKEN`).
- MailNet: set Gmail/Outlook token paths (see MCP/README.txt) then `magg server enable mailnet`.

## Convenience
- Scripts (magg, mcp-toolz, etc.) live in `C:\Users\treyt\AppData\Roaming\Python\Python314\Scripts`; add to PATH for shorter commands.
- To widen filesystem access, edit `files.args` in `.magg/config.json`.

This file is additive only; no files were moved or removed.
