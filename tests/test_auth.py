from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import User, UserRole
from app.security import get_password_hash
from app.services.users import authenticate_user


def test_authenticate_user_success_and_fail(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'auth.db'}", future=True)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, future=True)
    session = Session()
    try:
        user = User(
            username="admin",
            password_hash=get_password_hash("secret12345"),
            role=UserRole.admin.value,
            is_active=True,
        )
        session.add(user)
        session.commit()

        ok = authenticate_user(session, "admin", "secret12345")
        assert ok is not None
        bad = authenticate_user(session, "admin", "wrong")
        assert bad is None
    finally:
        session.close()
        engine.dispose()
