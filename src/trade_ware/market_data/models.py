"""Provider-neutral market-data domain models."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class MarketQuote:
    """Represent a normalized quote returned by a market-data provider."""

    symbol: str
    price: Decimal
    open: Decimal | None
    high: Decimal | None
    low: Decimal | None
    previous_close: Decimal | None
    change: Decimal | None
    change_percent: Decimal | None
    timestamp: datetime | None


@dataclass(frozen=True, slots=True)
class HistoricalPrice:
    """Represent one normalized OHLCV candle."""

    symbol: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal | None


@dataclass(frozen=True, slots=True)
class NewsItem:
    """Represent a normalized news article."""

    headline: str
    url: str
    source: str | None
    published_at: datetime | None
    summary: str | None


@dataclass(frozen=True, slots=True)
class PriceUpdate:
    """Represent a live provider price update."""

    symbol: str
    price: Decimal
    timestamp: datetime
