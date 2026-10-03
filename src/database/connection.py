"""
SQLAlchemy Session and Connection Management Module.
Provides SQLAlchemy 2.x engine, sessionmaker, context managers, and FastAPI dependency generators.
"""

from typing import Generator
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.database.config import settings

# Construct connect_args to fail fast (1s timeout) if PostgreSQL is offline
connect_args = {}
if "postgresql" in settings.database_url:
    connect_args["connect_timeout"] = 1

# Create SQLAlchemy 2.x engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    connect_args=connect_args,
    future=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True
)


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager providing safe SQLAlchemy session handling.
    Automatically commits on success and rolls back on exception.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding a database session per request.
    Handles rollback on exception and guaranteed closure.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
