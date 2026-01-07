# nixstrav-mng — Agent Instructions (Ralph Wiggum mode)

## Speak style
Short sentences. Say the obvious. Name risks. Then do the fix.

## Non-negotiable constraints
1) CF601 USB is on the operator PC. Server never talks to operator USB.
2) Enrollment must work from a browser on any LAN PC.
3) Keyboard-wedge is the default enrollment mode. Always works.
4) WebSerial/WebUSB are optional. Require HTTPS (secure context) and limited browser support.
5) Ubuntu 24.04 uses PEP 668. Do not pip-install system-wide. Use venv (or container venv).
6) Tests must run from repo root. Prefer pytest.ini forcing testpaths=tests.

## Deliverables are code + docs (always)
Every PR must update documentation files in-repo. No exceptions.
Maintain these files:

- docs/PRD.md                      (product truth; updated when behavior changes)
- docs/ARCHITECTURE.md             (components, data flows, ports, trust boundaries)
- docs/ENROLLMENT.md               (Mode A/B/C, browser constraints, troubleshooting)
- docs/SECURITY.md                 (auth, session, CSRF, LAN-only, TLS choices)
- docs/DEV_SETUP.md                (Dockerfile.dev, how to run tests, common gotchas)
- docs/OPERATIONS.md               (systemd, env vars, backup/restore, log locations)
- docs/AGENT_CONTEXT.md            (current state + invariants + open decisions)
- docs/CHANGELOG.md                (human-readable changes per merge to main)
- docs/ADR/0001-*.md               (Architecture Decision Records for non-trivial choices)

Doc rule:
- If you change behavior: update PRD + relevant docs in the same commit/PR.
- If you discover a gotcha: add it to DEV_SETUP.md and/or ENROLLMENT.md.
- If you make a design decision: add an ADR.

## Repository hygiene tasks (must do early)
- Ensure repo root is /workspace and contains .git.
- Add pytest.ini with:
  [pytest]
  testpaths = tests
- Add Makefile (or task runner) with targets:
  - make test
  - make run
  - make format (optional)
- Add GitHub Actions CI:
  - on PR: install deps, run pytest -q

## Implementation priorities
1) Enrollment Mode A is bulletproof (normalize EPC, debounce, alias suggest, CRUD tags).
2) known_tags.json writes are atomic and never corrupt.
3) Dashboard status is correct and configurable.
4) Auth + audit is correct.
5) Mode B (cf601d) works when possible; UI warns about CORS/mixed content.
6) Mode C (WebSerial/WebUSB) is optional; feature-detect; fallback to Mode A.

## Definition of Done for any change
- tests pass: pytest -q
- docs updated (see list)
- no server-side USB assumptions
- PR description includes: what changed, why, risks, how to test

“Przejazd po kodzie” — co jest teraz prawdą (i gdzie łatwo wpaść na minę)

Masz teraz dwa możliwe “rooty” w kontenerze (/workspace i /workspace/nixstrav-mng). To tworzy konflikty kolekcji testów (już to widziałeś). Dodaj pytest.ini i w docs napisz: uruchamiaj testy z root repo. 
Stack Overflow
+1

Jeśli chcesz utrzymać WebSerial/WebUSB: musisz mieć plan TLS, bo inaczej te API są zablokowane. 
developer.mozilla.org
+2
developer.mozilla.org
+2

PEP 668: venv jest standardem, inaczej pip krzyczy. 
Python Enhancement Proposals (PEPs)
+1
