import subprocess
from datetime import datetime
from typing import Any, Dict, List

from .events import last_events_per_reader, recent_errors


def check_service_status(service_name: str) -> Dict[str, Any]:
    try:
        result = subprocess.run(
            ["systemctl", "is-active", service_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            text=True,
        )
        status = result.stdout.strip() or result.stderr.strip()
        return {"name": service_name, "active": status == "active", "raw": status}
    except FileNotFoundError:
        return {"name": service_name, "active": False, "raw": "systemctl-not-found"}


def reader_status_heuristic(events_db: str) -> List[Dict[str, Any]]:
    readers = last_events_per_reader(events_db)
    now = datetime.utcnow()
    for r in readers:
        last = r.get("last_event")
        if last:
            try:
                dt = datetime.fromisoformat(last)
                delta = (now - dt).total_seconds()
                if delta < 90:
                    r["state"] = "green"
                elif delta < 300:
                    r["state"] = "yellow"
                else:
                    r["state"] = "red"
            except Exception:
                r["state"] = "unknown"
        else:
            r["state"] = "unknown"
    return readers


def problems(events_db: str, limit: int = 10) -> List[Dict[str, Any]]:
    return recent_errors(events_db, limit=limit)
