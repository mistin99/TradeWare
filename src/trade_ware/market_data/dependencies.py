"""FastAPI dependency helpers for market-data services."""

from functools import lru_cache

from redis.asyncio import Redis

from trade_ware.core.config import settings
from trade_ware.database.session import SessionFactory
from trade_ware.market_data.factory import MarketDataProviderFactory
from trade_ware.market_data.redis_cache import RedisPriceCache
from trade_ware.market_data.service import MarketDataService

redis_client = Redis.from_url(settings.redis_url, decode_responses=True)


@lru_cache
def get_market_data_service() -> MarketDataService:
    """Build the application service with configured provider and shared cache."""
    provider = MarketDataProviderFactory.create(settings)
    return MarketDataService(
        provider,
        RedisPriceCache(redis_client, int(settings.market_data_cache_ttl_seconds)),
        SessionFactory,
    )
