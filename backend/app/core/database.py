import os
import datetime
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

db_url = settings.database_url
connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}

# Ensure data directory exists if using local sqlite file
if db_url.startswith("sqlite:///") and ":memory:" not in db_url:
    path = db_url.replace("sqlite:///", "")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

engine = create_engine(db_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db() -> None:
    from app.models import entities  # noqa: F401
    Base.metadata.create_all(bind=engine)
