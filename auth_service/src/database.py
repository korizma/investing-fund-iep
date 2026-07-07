import os
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base


_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_database_url() -> str:
    database_url = os.environ.get("DATABASE_URL")

    if database_url is None or database_url == "":
        raise RuntimeError("DATABASE_URL environment variable is not set.")

    return database_url


def get_engine() -> Engine:
    global _engine

    if _engine is None:
        _engine = create_engine(get_database_url(), pool_pre_ping=True)

    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory

    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=get_engine(),
            expire_on_commit=False,
        )

    return _session_factory


@contextmanager
def session_scope() -> Iterator[Session]:
    session = get_session_factory()()

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_database() -> None:
    Base.metadata.create_all(bind=get_engine())
