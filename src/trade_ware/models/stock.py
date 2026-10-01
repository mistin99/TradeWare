"""Copyright (c) 2026 TradeWare contributors.

SQLAlchemy model for the application's supported stock universe.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from trade_ware.database.base import Base


class Stock(Base):
    """Represent a stock symbol that market-data jobs may refresh."""

    __tablename__ = "stocks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    symbol: Mapped[str] = mapped_column(
        String(32), unique=True, index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    exchange: Mapped[str] = mapped_column(String(64), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(32), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
