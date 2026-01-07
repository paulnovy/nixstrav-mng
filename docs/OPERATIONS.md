# Operations

## Systemd
- Unit file: systemd/nixstrav-mng.service
- Environment file: /etc/nixstrav-mng.env
- Enable: systemctl daemon-reload; systemctl enable --now nixstrav-mng

## Paths / data
- mng.db: management DB (read/write)
- known_tags.json: export/compat; writes are atomic and use .lock
- events.db: read-only input from nixstrav core
- config.json: UI config (if enabled)

## Backups
- Stop service or snapshot filesystem.
- Backup mng.db, known_tags.json, config.json.
- events.db is owned by nixstrav core; do not modify.

## Logs and health
- Logs in journald: journalctl -u nixstrav-mng
- Health endpoint: /api/v1/system/heartbeat
