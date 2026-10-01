"""Finnhub REST market-data provider."""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx

from trade_ware.market_data.exceptions import InvalidSymbolError
from trade_ware.market_data.http import request_json
from trade_ware.market_data.models import (
    HistoricalPrice,
    MarketQuote,
    NewsItem,
)
from trade_ware.market_data.provider import MarketDataProvider


class FinnhubProvider(MarketDataProvider):
    """Adapt Finnhub REST responses to TradeWare domain models."""

    base_url = "https://finnhub.io/api/v1"

    def __init__(
        self,
        api_key: str,
        client: httpx.AsyncClient | None = None,
        timeout_seconds: float = 10.0,
    ) -> None:
        """Create a provider with an injected or owned HTTP client."""
        self.api_key = api_key
        self.client = client or httpx.AsyncClient(timeout=timeout_seconds)
        self._owns_client = client is None

    async def aclose(self) -> None:
        """Close the internally owned HTTP client."""
        if self._owns_client:
            await self.client.aclose()

    async def get_quote(self, symbol: str) -> MarketQuote:
        """Fetch and normalize a Finnhub quote."""
        payload = await request_json(
            self.client,
            "finnhub",
            "quote",
            f"{self.base_url}/quote",
            {"symbol": symbol, "token": self.api_key},
        )
        if not isinstance(payload, dict) or not payload.get("c"):
            raise InvalidSymbolError("Finnhub quote was empty or malformed")
        return MarketQuote(
            symbol=symbol,
            price=_decimal(payload, "c"),
            open=_optional_decimal(payload, "o"),
            high=_optional_decimal(payload, "h"),
            low=_optional_decimal(payload, "l"),
            previous_close=_optional_decimal(payload, "pc"),
            change=_optional_decimal(payload, "d"),
            change_percent=_optional_decimal(payload, "dp"),
            timestamp=_timestamp(payload.get("t")),
        )

    async def get_history(
        self,
        symbol: str,
        interval: str = "1day",
        start: date | None = None,
        end: date | None = None,
    ) -> list[HistoricalPrice]:
        """Fetch and normalize Finnhub candle data."""
        resolution = {
            "1min": "1",
            "5min": "5",
            "15min": "15",
            "1hour": "60",
            "1day": "D",
        }.get(interval, interval)
        end_date = end or datetime.now(timezone.utc).date()
        start_date = start or (end_date - timedelta(days=30))
        payload = await request_json(
            self.client,
            "finnhub",
            "history",
            f"{self.base_url}/stock/candle",
            {
                "symbol": symbol,
                "resolution": resolution,
                "from": int(
                    datetime.combine(
                        start_date, datetime.min.time(), tzinfo=timezone.utc
                    ).timestamp()
                ),
                "to": int(
                    datetime.combine(
                        end_date, datetime.max.time(), tzinfo=timezone.utc
                    ).timestamp()
                ),
                "token": self.api_key,
            },
        )
        if not isinstance(payload, dict) or payload.get("s") != "ok":
            raise InvalidSymbolError("Finnhub history was empty or malformed")
        timestamps = payload.get("t", [])
        return [
            HistoricalPrice(
                symbol=symbol,
                timestamp=_timestamp(timestamp) or datetime.now(timezone.utc),
                open=_decimal_at(payload, "o", index),
                high=_decimal_at(payload, "h", index),
                low=_decimal_at(payload, "l", index),
                close=_decimal_at(payload, "c", index),
                volume=_optional_decimal_at(payload, "v", index),
            )
            for index, timestamp in enumerate(timestamps)
        ]

    async def get_news(
        self,
        symbol: str,
        start: date | None = None,
        end: date | None = None,
    ) -> list[NewsItem]:
        """Fetch and normalize Finnhub company news."""
        end_date = end or datetime.now(timezone.utc).date()
        start_date = start or (end_date - timedelta(days=30))
        payload = await request_json(
            self.client,
            "finnhub",
            "news",
            f"{self.base_url}/company-news",
            {
                "symbol": symbol,
                "from": start_date.isoformat(),
                "to": end_date.isoformat(),
                "token": self.api_key,
            },
        )
        if not isinstance(payload, list):
            raise InvalidSymbolError("Finnhub news was malformed")
        return [
            NewsItem(
                headline=str(article.get("headline", "")),
                url=str(article.get("url", "")),
                source=article.get("source"),
                published_at=_timestamp(article.get("datetime")),
                summary=article.get("summary"),
            )
            for article in payload
            if isinstance(article, dict)
        ]


def _decimal(payload: dict[str, Any], key: str) -> Decimal:
    """Read a required decimal field from Finnhub data."""
    try:
        return Decimal(str(payload[key]))
    except (KeyError, InvalidOperation, TypeError) as exc:
        raise InvalidSymbolError(f"Missing Finnhub field: {key}") from exc


def _optional_decimal(payload: dict[str, Any], key: str) -> Decimal | None:
    """Read an optional decimal field from Finnhub data."""
    if payload.get(key) in (None, ""):
        return None
    try:
        return Decimal(str(payload[key]))
    except InvalidOperation as exc:
        raise InvalidSymbolError(f"Malformed Finnhub field: {key}") from exc


def _decimal_at(payload: dict[str, Any], key: str, index: int) -> Decimal:
    """Read a required indexed Finnhub candle value."""
    try:
        return Decimal(str(payload[key][index]))
    except (KeyError, IndexError, InvalidOperation, TypeError) as exc:
        raise InvalidSymbolError(
            f"Malformed Finnhub history field: {key}"
        ) from exc


def _optional_decimal_at(
    payload: dict[str, Any], key: str, index: int
) -> Decimal | None:
    """Read an optional indexed Finnhub candle value."""
    try:
        value = payload.get(key, [])[index]
    except (IndexError, TypeError):
        return None
    return None if value is None else Decimal(str(value))


def _timestamp(value: Any) -> datetime | None:
    """Convert a Unix timestamp to UTC."""
    if value in (None, ""):
        return None
    return datetime.fromtimestamp(float(value), tz=timezone.utc)
