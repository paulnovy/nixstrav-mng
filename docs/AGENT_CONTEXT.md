# Agent Context

## Current State
- Repo root: /workspace/nixstrav-mng (contains .git). There is also /workspace as a parent.
- Stack: FastAPI + Jinja, SQLite; no external assets.
- Enrollment UI at /enroll supports keyboard wedge, local reader bridge (localhost), and WebSerial (optional).
- Added Windows reader bridge under tools/reader-bridge (bridge.py + install.bat/run.bat).
- known_tags.json sync uses atomic write + .lock.
- events.db is accessed read-only via sqlite mode=ro.
- CI: GitHub Actions runs pytest -q on pull requests.

## Invariants (must hold)
- CF601 USB is on the operator PC. Server never talks to operator USB.
- Enrollment must work from a browser on any LAN PC.
- Mode A (keyboard wedge) is default and always works.
- WebSerial/WebUSB are optional; require HTTPS secure context.
- PEP 668: use venv, no system-wide pip.
- Tests run from repo root; pytest.ini sets testpaths=tests.

## Open Decisions / Risks
- TLS plan for LAN (reverse proxy, cert distribution) to unlock WebSerial/WebUSB.
- CORS policy for cf601d (exact allowed origin list).

## Agent Instructions
- Pełny prompt agenta znajduje się w `AGENTS.md` i jest źródłem prawdy dla workflow Codexa.
