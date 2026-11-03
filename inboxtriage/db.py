from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from inboxtriage.config import get_settings
from inboxtriage.models import Base


def get_engine(database_url: str | None = None) -> Engine:
    url = database_url or get_settings()["database_url"]
    return create_engine(url, future=True)


def get_session_factory(database_url: str | None = None):
    engine = get_engine(database_url)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db(database_url: str | None = None) -> Engine:
    engine = get_engine(database_url)
    Base.metadata.create_all(bind=engine)
    return engine


def get_session(database_url: str | None = None) -> Session:
    session_factory = get_session_factory(database_url)
    return session_factory()
