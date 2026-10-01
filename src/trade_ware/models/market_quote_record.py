"""Copyright (c) 2026 TradeWare contributors.

SQLAlchemy model for persisted market quote snapshots.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from trade_ware.database.base import Base


class MarketQuoteRecord(Base):
    """Store a normalized quote snapshot for historical reads."""

    __tablename__ = "market_quote_records"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    open: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    high: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    low: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    previous_close: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    change: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    change_percent: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    provider_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
