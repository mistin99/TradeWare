"""Application service for Redis-backed market data and quote history."""

from datetime import date, datetime, timezone

from sqlalchemy import select

from trade_ware.market_data.models import (
    HistoricalPrice,
    MarketQuote,
    NewsItem,
    PriceUpdate,
)
from trade_ware.market_data.provider import MarketDataProvider
from trade_ware.market_data.redis_cache import RedisPriceCache
from trade_ware.models.market_quote_record import MarketQuoteRecord
from trade_ware.models.stock import Stock


class MarketDataService:
    """Expose provider-neutral market data to application code."""

    def __init__(
        self,
        provider: MarketDataProvider,
        cache: RedisPriceCache,
        session_factory,
    ) -> None:
        """Inject a provider, Redis cache, and database session factory."""
        self.provider = provider
        self.cache = cache
        self.session_factory = session_factory

    async def get_latest_price(self, symbol: str) -> PriceUpdate:
        """Return Redis price data without calling an external provider."""
        return await self.cache.get(symbol)

    async def refresh_quote(self, symbol: str) -> MarketQuote:
        """Fetch a quote, write it to Redis, and persist a history snapshot."""
        quote = await self.provider.get_quote(symbol)
        update = PriceUpdate(
            symbol=quote.symbol,
            price=quote.price,
            timestamp=quote.timestamp or datetime.now(timezone.utc),
        )
        await self.cache.set(update)
        with self.session_factory() as db:
            db.add(
                MarketQuoteRecord(
                    symbol=quote.symbol.upper(),
                    price=quote.price,
                    open=quote.open,
                    high=quote.high,
                    low=quote.low,
                    previous_close=quote.previous_close,
                    change=quote.change,
                    change_percent=quote.change_percent,
                    provider_timestamp=quote.timestamp,
                )
            )
            db.commit()
        return quote

    async def refresh_symbol_universe(self) -> list[str]:
        """Sync active database stocks into the persistent Redis symbol set."""
        with self.session_factory() as db:
            symbols = list(
                db.scalars(
                    select(Stock.symbol)
                    .where(Stock.is_active.is_(True))
                    .order_by(Stock.symbol)
                ).all()
            )
        await self.cache.replace_symbols(symbols)
        return symbols

    async def get_cached_symbols(self) -> list[str]:
        """Return the currently cached stock symbol universe."""
        return await self.cache.get_symbols()

    async def get_quote(self, symbol: str) -> MarketQuote:
        """Return the provider-normalized quote."""
        return await self.provider.get_quote(symbol)

    async def get_history(
        self,
        symbol: str,
        limit: int = 100,
    ) -> list[HistoricalPrice]:
        """Return persisted quote snapshots ordered newest first."""
        with self.session_factory() as db:
            records = db.scalars(
                select(MarketQuoteRecord)
                .where(MarketQuoteRecord.symbol == symbol.upper())
                .order_by(MarketQuoteRecord.recorded_at.desc())
                .limit(limit)
            ).all()
        return [
            HistoricalPrice(
                symbol=record.symbol,
                timestamp=record.provider_timestamp or record.recorded_at,
                open=record.open or record.price,
                high=record.high or record.price,
                low=record.low or record.price,
                close=record.price,
                volume=None,
            )
            for record in records
        ]

    async def get_news(
        self,
        symbol: str,
        start: date | None = None,
        end: date | None = None,
    ) -> list[NewsItem]:
        """Return normalized news items."""
        return await self.provider.get_news(symbol, start, end)
