# Phase 7 Unified System

This folder contains the Phase 7 web dashboard: a React frontend and a Flask backend that orchestrates study sessions and Anki integration.

## Structure
- `backend/` Flask API (runs on port 5000)
- `frontend/` React app (dev server on port 3000, proxies to 5000)

## Requirements
- Python 3.12 (recommended for current pins)
- Node.js 18+
- Optional: Anki desktop with AnkiConnect (port 8765) for local add; or AnkiWeb credentials for fallback.

## Setup
1) Python venv and dependencies
   - `py -3.12 -m venv .venv`
   - `.\.venv\Scripts\Activate.ps1`
   - `python -m pip install --upgrade pip`
   - `python -m pip install -r requirements.txt`

2) Backend environment variables
   - Copy `backend/.env.example` to `backend/.env`
   - Set values (leave blank if not using):
     - `ANTHROPIC_API_KEY=`
     - `ANKI_EMAIL=`
     - `ANKI_PASSWORD=`
   - Note: Defaults have been removed; missing values will skip that integration.

3) Run the backend
   - From `phase7_unified_system/`: `python backend\app.py`
   - Health check: `http://localhost:5000/api/health`

4) Run the frontend
   - `cd frontend`
   - `npm install`
   - `npm start`
   - Open `http://localhost:3000`

## Endpoints (selected)
- `GET /api/health` – status and config flags
- `GET /api/dashboard` – dashboard data
- `GET /api/courses` – list of courses
- `POST /api/study/plan` – returns a PERRIO plan for a course
- `POST /api/study/execute` – simulates a study session and attempts to add cards to Anki
- `GET /api/anki/status` – Anki connection status
- `POST /api/anki/add-cards` – add provided cards to Anki

## Anki Integration
- Prefers AnkiConnect (Anki desktop) if detected.
- Falls back to AnkiWeb only if `ANKI_EMAIL` and `ANKI_PASSWORD` are set.
- If neither is available, the backend still runs and updates in-memory counters.

## Notes
- Anthropic client is lazy-initialized to avoid import-time httpx compatibility issues. It will only be created if `ANTHROPIC_API_KEY` is set and used by routes that need it.
- Console encoding is set to UTF-8 to prevent Unicode errors on Windows.

## What’s Left / TODOs
- Add a Claude test route once `ANTHROPIC_API_KEY` is configured.
- Replace simulated card generation with real pipeline wiring (Anatomy MCP + DrCodePT generators).
- Clean up legacy unicode prints in logs.
- Add persistence (DB) for study history instead of in-memory state.
- Optional: convert backend package imports to module-safe (`python -m backend.app`).

