"""Database session configuration."""

import logging
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from trade_ware.core.config import settings
from trade_ware.database.base import Base

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.resolved_database_url,
    pool_pre_ping=True,
    future=True,
)

SessionFactory = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def initialize_database() -> None:
    """Create tables for the configured database if needed."""
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as exc:  
        logger.warning("Database initialization skipped: %s", exc)


def get_db() -> Generator[Session, None, None]:
    """Get a database session."""
    db = SessionFactory()
    try:
        yield db
    finally:
        db.close()
