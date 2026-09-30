"""Tests for the database session configuration."""

from sqlalchemy import create_engine, text

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
)


def test_db_connection():
    """Tests that the SQLAlchemy engine can execute a basic query."""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar_one() == 1
