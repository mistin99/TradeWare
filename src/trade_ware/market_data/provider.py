"""Provider strategy interface for normalized market data."""

from abc import ABC, abstractmethod
from datetime import date

from trade_ware.market_data.models import (
    HistoricalPrice,
    MarketQuote,
    NewsItem,
)


class MarketDataProvider(ABC):
    """Strategy interface implemented by each external market-data provider."""

    @abstractmethod
    async def get_quote(self, symbol: str) -> MarketQuote:
        """Return the latest quote for a symbol."""

    @abstractmethod
    async def get_history(
        self,
        symbol: str,
        interval: str = "1day",
        start: date | None = None,
        end: date | None = None,
    ) -> list[HistoricalPrice]:
        """Return normalized historical candles."""

    @abstractmethod
    async def get_news(
        self,
        symbol: str,
        start: date | None = None,
        end: date | None = None,
    ) -> list[NewsItem]:
        """Return normalized news articles."""
