from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings

db_path = settings.mng_db
db_path.parent.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{db_path}"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}, future=True
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

Base = declarative_base()


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
