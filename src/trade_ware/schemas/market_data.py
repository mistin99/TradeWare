"""API response schemas for Redis-backed market data."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class LatestPriceResponse(BaseModel):
    """Return the latest price stored in Redis."""

    symbol: str
    price: Decimal
    timestamp: datetime


class HistoricalPriceResponse(BaseModel):
    """Return one persisted quote snapshot."""

    symbol: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal | None
