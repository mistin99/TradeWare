"""Twelve Data REST market-data provider."""

from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx

from trade_ware.market_data.exceptions import InvalidSymbolError
from trade_ware.market_data.http import request_json
from trade_ware.market_data.models import HistoricalPrice, MarketQuote, NewsItem
from trade_ware.market_data.provider import MarketDataProvider


class TwelveDataProvider(MarketDataProvider):
    """Adapt Twelve Data REST responses to TradeWare domain models."""

    base_url = "https://api.twelvedata.com"

    def __init__(
        self,
        api_key: str,
        client: httpx.AsyncClient | None = None,
        timeout_seconds: float = 10.0,
    ) -> None:
        """Create a provider with an injected or internally owned HTTP client."""
        self.api_key = api_key
        self.client = client or httpx.AsyncClient(timeout=timeout_seconds)
        self._owns_client = client is None

    async def aclose(self) -> None:
        """Close the internally owned HTTP client."""
        if self._owns_client:
            await self.client.aclose()

    async def get_quote(self, symbol: str) -> MarketQuote:
        """Fetch and normalize a Twelve Data quote."""
        payload = await request_json(
            self.client,
            "twelve_data",
            "quote",
            f"{self.base_url}/quote",
            {"symbol": symbol, "apikey": self.api_key},
        )
        if not isinstance(payload, dict):
            raise InvalidSymbolError("Twelve Data quote was malformed")
        return MarketQuote(
            symbol=str(payload.get("symbol", symbol)),
            price=_decimal(payload, "close"),
            open=_optional_decimal(payload, "open"),
            high=_optional_decimal(payload, "high"),
            low=_optional_decimal(payload, "low"),
            previous_close=_optional_decimal(payload, "previous_close"),
            change=_optional_decimal(payload, "change"),
            change_percent=_optional_decimal(payload, "percent_change"),
            timestamp=_parse_datetime(payload.get("datetime")),
        )

    async def get_history(
        self,
        symbol: str,
        interval: str = "1day",
        start: date | None = None,
        end: date | None = None,
    ) -> list[HistoricalPrice]:
        """Fetch and normalize Twelve Data time-series values."""
        params: dict[str, Any] = {
            "symbol": symbol,
            "interval": interval,
            "apikey": self.api_key,
        }
        if start:
            params["start_date"] = start.isoformat()
        if end:
            params["end_date"] = end.isoformat()
        payload = await request_json(
            self.client,
            "twelve_data",
            "history",
            f"{self.base_url}/time_series",
            params,
        )
        values = payload.get("values") if isinstance(payload, dict) else None
        if not isinstance(values, list):
            raise InvalidSymbolError("Twelve Data history was malformed")
        return [_history_value(symbol, value) for value in values]

    async def get_news(
        self,
        symbol: str,
        start: date | None = None,
        end: date | None = None,
    ) -> list[NewsItem]:
        """Fetch and normalize Twelve Data news results."""
        params: dict[str, Any] = {"symbol": symbol, "apikey": self.api_key}
        if start:
            params["start_date"] = start.isoformat()
        if end:
            params["end_date"] = end.isoformat()
        payload = await request_json(
            self.client,
            "twelve_data",
            "news",
            f"{self.base_url}/news",
            params,
        )
        articles = payload.get("data") if isinstance(payload, dict) else payload
        if not isinstance(articles, list):
            raise InvalidSymbolError("Twelve Data news was malformed")
        return [
            NewsItem(
                headline=str(article.get("title", "")),
                url=str(article.get("url", "")),
                source=article.get("source"),
                published_at=_parse_datetime(article.get("published_at")),
                summary=article.get("description"),
            )
            for article in articles
            if isinstance(article, dict)
        ]


def _decimal(payload: dict[str, Any], key: str) -> Decimal:
    """Read a required decimal field from a provider payload."""
    try:
        return Decimal(str(payload[key]))
    except (KeyError, InvalidOperation, TypeError) as exc:
        raise InvalidSymbolError(f"Missing Twelve Data field: {key}") from exc


def _optional_decimal(payload: dict[str, Any], key: str) -> Decimal | None:
    """Read an optional decimal field from a provider payload."""
    if payload.get(key) in (None, ""):
        return None
    try:
        return Decimal(str(payload[key]))
    except InvalidOperation as exc:
        raise InvalidSymbolError(f"Malformed Twelve Data field: {key}") from exc


def _parse_datetime(value: Any) -> datetime | None:
    """Parse common ISO or provider timestamp values."""
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _history_value(symbol: str, value: Any) -> HistoricalPrice:
    """Normalize one Twelve Data historical value."""
    if not isinstance(value, dict):
        raise InvalidSymbolError("Twelve Data history value was malformed")
    return HistoricalPrice(
        symbol=symbol,
        timestamp=_parse_datetime(value.get("datetime")) or datetime.now(timezone.utc),
        open=_decimal(value, "open"),
        high=_decimal(value, "high"),
        low=_decimal(value, "low"),
        close=_decimal(value, "close"),
        volume=_optional_decimal(value, "volume"),
    )
