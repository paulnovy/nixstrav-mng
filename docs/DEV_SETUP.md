# Dev Setup

## Requirements
- Python 3.12
- Ubuntu 24.04 uses PEP 668: do not pip install system-wide. Use venv or container venv.

## Setup
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

Optional: copy .env.example to .env and adjust paths/secrets.

## Dockerfile.dev
- Not present in repo yet. If added later, document build/run steps here.

## Run
make run
# or
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

## Notes
- SessionMiddleware comes from Starlette and requires itsdangerous.
- Start the server from repo root (/workspace/nixstrav-mng).

## Tests
- Run from repo root (important to avoid pytest import mismatch).
- pytest.ini enforces testpaths=tests.
- Command: make test or pytest -q.

## Repo roots
In some containers both /workspace and /workspace/nixstrav-mng exist. Always run tests and tooling from /workspace/nixstrav-mng (repo root with .git).
