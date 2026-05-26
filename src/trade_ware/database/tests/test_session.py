"""Tests for the database session configuration."""

from trade_ware.database.session import engine


def test_db_connection():
    """Tests that the database connection can be established."""
    with engine.connect() as conn:
        result = conn.exec_driver_sql("SELECT 1")
        assert result.scalar() == 1
