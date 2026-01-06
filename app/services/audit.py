import json
from typing import Any, Optional

from sqlalchemy.orm import Session

from ..models import AuditLog, User


def log_action(
    session: Session,
    user: Optional[User],
    action: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    before: Any = None,
    after: Any = None,
    ip: Optional[str] = None,
) -> None:
    entry = AuditLog(
        user=user.username if user else None,
        user_id=user.id if user else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before_json=json.dumps(before) if before is not None else None,
        after_json=json.dumps(after) if after is not None else None,
        ip=ip,
    )
    session.add(entry)
    session.commit()
