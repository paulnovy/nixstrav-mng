# Architecture

## Components
- Browser (LAN clients)
- nixstrav-mng app server (FastAPI + Jinja) on marianserwer
- mng.db (SQLite) for management data
- known_tags.json (export/compat) on server filesystem
- events.db (read-only) from nixstrav core
- cf601d local agent on operator PC (optional)
- CF601 reader physically connected to operator PC

## Data flows
- Browser -> nixstrav-mng: HTML UI + JSON APIs
- nixstrav-mng -> mng.db: read/write
- nixstrav-mng -> known_tags.json: atomic write (tmp + fsync + rename)
- nixstrav-mng -> events.db: read-only (sqlite ro)
- Browser -> cf601d (Mode B): HTTP to 127.0.0.1 on operator PC
- Browser -> WebSerial/WebUSB (Mode C): direct hardware from client

## Ports
- nixstrav-mng: 8000 (behind reverse proxy/TLS)
- cf601d: 8888 on operator PC (localhost)
- reverse proxy TLS: 443 (optional but needed for WebSerial/WebUSB)

## Trust boundaries
- Server never touches operator USB; hardware access stays in browser or local agent.
- LAN only access; block public ingress.
- events.db is external input; treat as read-only and potentially incomplete.

## Enrollment rules
- Keyboard‑wedge is default.
- EPC accepted after **3 confirmations in 3s** and must be **24 hex**.
- Skan akceptowany po Enter, fokus utrzymywany na polu.
