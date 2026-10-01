"""Redis-backed latest-price storage for the market-data layer."""

import json
from datetime import datetime, timezone
from decimal import Decimal

from redis.asyncio import Redis

from trade_ware.market_data.exceptions import StaleMarketDataError
from trade_ware.market_data.models import PriceUpdate


class RedisPriceCache:
    """Store latest normalized prices in Redis with an expiration time."""

    def __init__(self, client: Redis, ttl_seconds: int) -> None:
        """Create a Redis cache using an injected client."""
        self.client = client
        self.ttl_seconds = ttl_seconds

    def _key(self, symbol: str) -> str:
        """Build the namespaced Redis key for a symbol."""
        return f"tradeware:market:price:{symbol.upper()}"

    @property
    def symbols_key(self) -> str:
        """Return the Redis key for the cached stock symbol universe."""
        return "tradeware:market:symbols"

    async def replace_symbols(self, symbols: list[str]) -> None:
        """Replace the cached symbol set without assigning an expiration."""
        normalized = sorted({symbol.upper() for symbol in symbols})
        pipeline = self.client.pipeline()
        pipeline.delete(self.symbols_key)
        if normalized:
            pipeline.sadd(self.symbols_key, *normalized)
        await pipeline.execute()

    async def get_symbols(self) -> list[str]:
        """Return the cached stock symbols in stable order."""
        symbols = await self.client.smembers(self.symbols_key)
        return sorted(symbols)

    async def set(self, update: PriceUpdate) -> None:
        """Store a price update as JSON with a Redis TTL."""
        payload = {
            "symbol": update.symbol.upper(),
            "price": str(update.price),
            "timestamp": update.timestamp.astimezone(timezone.utc).isoformat(),
        }
        await self.client.set(
            self._key(update.symbol), json.dumps(payload), ex=self.ttl_seconds
        )

    async def get(self, symbol: str) -> PriceUpdate:
        """Read a cached price or raise when Redis has no current value."""
        raw = await self.client.get(self._key(symbol))
        if raw is None:
            raise StaleMarketDataError(f"No current Redis price for {symbol}")
        payload = json.loads(raw)
        return PriceUpdate(
            symbol=payload["symbol"],
            price=Decimal(payload["price"]),
            timestamp=datetime.fromisoformat(payload["timestamp"]),
        )
