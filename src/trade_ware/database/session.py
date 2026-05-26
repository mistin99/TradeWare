"""Database session configuration."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from trade_ware.core.config import settings
DATABASE_URL = (
    "postgresql+psycopg://postgres:password@localhost:5432/mydb"
)

engine = create_engine(settings.database_url)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)