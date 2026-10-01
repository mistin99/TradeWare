"""Unit tests for providers, cache, service injection, and stream management."""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from trade_ware.market_data.exceptions import InvalidSymbolError, StaleMarketDataError
from trade_ware.market_data.models import MarketQuote
from trade_ware.market_data.providers.finnhub import FinnhubProvider
from trade_ware.market_data.providers.twelve_data import TwelveDataProvider
from trade_ware.market_data.redis_cache import RedisPriceCache
from trade_ware.market_data.service import MarketDataService
from trade_ware.market_data.stream import (
    FinnhubStream,
    MarketDataStreamManager,
)


def response(payload, status_code=200):
    """Create an HTTP response for an injected async client."""
    return httpx.Response(
        status_code,
        json=payload,
        request=httpx.Request("GET", "https://provider.test"),
    )


@pytest.mark.asyncio
async def test_twelve_data_quote_is_normalized():
    """Verify Twelve Data quote fields map to the domain model."""
    client = AsyncMock()
    client.get.return_value = response(
        {
            "symbol": "AAPL",
            "close": "227.34",
            "open": "226.0",
            "high": "228.0",
            "low": "225.0",
            "previous_close": "224.0",
            "change": "3.34",
            "percent_change": "1.49",
            "datetime": "2026-10-01T12:00:00Z",
        }
    )
    quote = await TwelveDataProvider("secret", client).get_quote("AAPL")
    assert quote.symbol == "AAPL"
    assert quote.price == Decimal("227.34")
    assert quote.change_percent == Decimal("1.49")
    assert client.get.call_args.kwargs["params"]["apikey"] == "secret"


@pytest.mark.asyncio
async def test_twelve_data_history_and_news_are_normalized():
    """Verify Twelve Data history and news parsing."""
    client = AsyncMock()
    client.get.side_effect = [
        response(
            {
                "values": [
                    {
                        "datetime": "2026-10-01",
                        "open": "1",
                        "high": "2",
                        "low": "0.5",
                        "close": "1.5",
                        "volume": "100",
                    }
                ]
            }
        ),
        response({"data": [{"title": "Headline", "url": "https://news.test"}]}),
    ]
    provider = TwelveDataProvider("secret", client)
    history = await provider.get_history("AAPL")
    news = await provider.get_news("AAPL")
    assert history[0].close == Decimal("1.5")
    assert news[0].headline == "Headline"


@pytest.mark.asyncio
async def test_finnhub_quote_history_and_news_are_normalized():
    """Verify Finnhub response formats map to shared domain models."""
    client = AsyncMock()
    client.get.side_effect = [
        response({"c": 10, "o": 9, "h": 11, "l": 8, "pc": 9.5, "d": 0.5, "dp": 5}),
        response(
            {
                "s": "ok",
                "t": [1727769600],
                "o": [1],
                "h": [2],
                "l": [0],
                "c": [1.5],
                "v": [10],
            }
        ),
        response(
            [{"headline": "News", "url": "https://news.test", "datetime": 1727769600}]
        ),
    ]
    provider = FinnhubProvider("secret", client)
    assert (await provider.get_quote("AAPL")).price == Decimal(10)
    assert (await provider.get_history("AAPL"))[0].close == Decimal("1.5")
    assert (await provider.get_news("AAPL"))[0].headline == "News"


@pytest.mark.asyncio
async def test_provider_http_and_malformed_errors_are_translated():
    """Verify providers do not leak raw HTTP or response errors."""
    client = AsyncMock()
    client.get.return_value = response({"status": "error", "message": "bad symbol"})
    with pytest.raises(InvalidSymbolError):
        await TwelveDataProvider("secret", client).get_quote("INVALID")


@pytest.mark.asyncio
async def test_service_uses_same_strategy_contract_for_any_provider():
    """Verify service behavior depends on the abstraction, not provider type."""
    provider = AsyncMock()
    provider.get_quote.return_value = MarketQuote(
        "AAPL", Decimal(10), None, None, None, None, None, None, None
    )
    redis = AsyncMock()
    session = MagicMock()
    session_factory = MagicMock(return_value=session)
    service = MarketDataService(
        provider, RedisPriceCache(redis, 30), session_factory
    )
    result = await service.refresh_quote("AAPL")
    assert result.price == Decimal(10)
    provider.get_quote.assert_awaited_once_with("AAPL")


@pytest.mark.asyncio
async def test_cache_stale_price_and_stream_deduplication():
    """Verify cache freshness and centralized duplicate subscription handling."""
    redis = AsyncMock()
    redis.get.return_value = None
    cache = RedisPriceCache(redis, 30)
    with pytest.raises(StaleMarketDataError):
        await cache.get("AAPL")
    stream = AsyncMock()
    manager = MarketDataStreamManager(stream, cache)
    await manager.subscribe(["aapl", "AAPL", "MSFT"])
    await manager.subscribe(["AAPL"])
    stream.subscribe.assert_awaited_once_with(["AAPL", "MSFT"])


@pytest.mark.asyncio
async def test_stream_messages_update_cache():
    """Verify provider WebSocket messages become cached domain updates."""
    websocket = AsyncMock()
    timestamp = datetime.now(timezone.utc).timestamp() * 1000
    websocket.recv.return_value = (
        f'{{"type":"trade","data":[{{"s":"AAPL","p":10,"t":{timestamp}}}]}}'.replace(
            "'", '"'
        )
    )
    redis = AsyncMock()
    cache = RedisPriceCache(redis, 30)
    manager = MarketDataStreamManager(FinnhubStream("secret", websocket), cache)
    updates = await manager.receive_once()
    assert updates[0].price == Decimal(10)
    redis.get.return_value = '{"symbol":"AAPL","price":"10","timestamp":"'
    redis.get.return_value += datetime.now(timezone.utc).isoformat() + '"}'
    assert (await cache.get("AAPL")).price == Decimal(10)
