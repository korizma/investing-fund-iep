import os
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base, User


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


def get_all_users() -> list[dict]:
    with session_scope() as session:
        users = session.query(User).order_by(User.id).all()

        return [
            {
                "id": user.id,
                "forename": user.forename,
                "surname": user.surname,
                "email": user.email,
                "password": user.password,
                "role": user.role,
            }
            for user in users
        ]

def init_database() -> None:
    Base.metadata.create_all(bind=get_engine())

    write_initial_data()
    print(get_all_users(), flush=True)

def write_initial_data():
    from .db_manip import create_user
    create_user('Scrooge', 'McDuck', 'onlymoney@gmail.com', 'evenmoremoney', 'director')
    
