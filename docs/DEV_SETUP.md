# Dev Setup

## Wymagania
- Python 3.12 (server)
- venv + pip

## Start
```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export DEV_INSECURE_COOKIES=true
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Reader Bridge (Windows) — awaryjnie
Jeśli keyboard‑wedge nie działa, użyj lokalnego bridge: `tools/reader-bridge/README.md`.
