"""Database session configuration."""

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from trade_ware.core.config import settings


engine = create_engine(
    settings.database_url,
    isolation_level="REPEATABLE READ",
    pool_pre_ping=True,
    pool_recycle=3600,
)

SessionFactory = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """Get a database session."""
    db = SessionFactory()
    try:
        yield db
    finally:
        db.close()
