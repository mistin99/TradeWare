"""Provider streaming abstractions and centralized subscription manager."""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import websockets

from trade_ware.market_data.models import PriceUpdate
from trade_ware.market_data.redis_cache import RedisPriceCache

logger = logging.getLogger(__name__)


class MarketDataStream(ABC):
    """Interface for one backend-owned provider WebSocket connection."""

    @abstractmethod
    async def connect(self) -> None:
        """Connect to the provider stream."""

    @abstractmethod
    async def subscribe(self, symbols: list[str]) -> None:
        """Subscribe to provider symbols."""

    @abstractmethod
    async def unsubscribe(self, symbols: list[str]) -> None:
        """Unsubscribe from provider symbols."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Close the provider stream."""

    @abstractmethod
    async def receive(self) -> list[PriceUpdate]:
        """Receive and normalize one provider message."""


class MarketDataStreamManager:
    """Maintain one provider connection and symbol subscriptions."""

    def __init__(self, stream: MarketDataStream, cache: RedisPriceCache) -> None:
        """Inject one stream strategy and one shared price cache."""
        self.stream = stream
        self.cache = cache
        self._symbols: set[str] = set()

    async def connect(self) -> None:
        """Connect the backend-owned provider stream."""
        await self.stream.connect()

    async def subscribe(self, symbols: list[str]) -> None:
        """Add only new symbols to the provider subscription."""
        normalized = {symbol.upper() for symbol in symbols}
        new_symbols = sorted(normalized - self._symbols)
        if new_symbols:
            await self.stream.subscribe(new_symbols)
            self._symbols.update(new_symbols)

    async def unsubscribe(self, symbols: list[str]) -> None:
        """Remove subscribed symbols and ignore unknown symbols."""
        normalized = {symbol.upper() for symbol in symbols}
        removed = sorted(normalized & self._symbols)
        if removed:
            await self.stream.unsubscribe(removed)
            self._symbols.difference_update(removed)

    async def receive_once(self) -> list[PriceUpdate]:
        """Receive updates once and write them to the centralized cache."""
        updates = await self.stream.receive()
        for update in updates:
            await self.cache.set(update)
        return updates

    async def disconnect(self) -> None:
        """Disconnect the provider stream."""
        await self.stream.disconnect()

    async def run(self, stop_event: asyncio.Event) -> None:
        """Consume updates and reconnect with bounded exponential backoff."""
        delay = 1.0
        while not stop_event.is_set():
            try:
                await self.connect()
                delay = 1.0
                while not stop_event.is_set():
                    await self.receive_once()
            except (
                OSError,
                ValueError,
                websockets.exceptions.WebSocketException,
            ) as exc:
                logger.warning("Market-data stream disconnected: %s", exc)
                await self.disconnect()
                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=delay)
                except asyncio.TimeoutError:
                    delay = min(delay * 2, 30.0)
        await self.disconnect()


class TwelveDataStream(MarketDataStream):
    """Backend-owned Twelve Data price WebSocket adapter."""

    url = "wss://ws.twelvedata.com/v1/quotes/price"

    def __init__(self, api_key: str, websocket=None) -> None:
        """Create a stream with an optional injected WebSocket test double."""
        self.api_key = api_key
        self.websocket = websocket

    def _require_websocket(self) -> Any:
        """Return the connected socket or raise a clear lifecycle error."""
        if self.websocket is None:
            raise RuntimeError("Twelve Data stream is not connected")
        return self.websocket

    async def connect(self) -> None:
        """Open the Twelve Data WebSocket when one was not injected."""
        if self.websocket is None:
            self.websocket = await websockets.connect(
                f"{self.url}?apikey={self.api_key}"
            )

    async def subscribe(self, symbols: list[str]) -> None:
        """Subscribe to symbols on the provider connection."""
        websocket = self._require_websocket()
        await websocket.send(
            json.dumps(
                {
                    "action": "subscribe",
                    "params": {"symbols": ",".join(symbols)},
                }
            )
        )

    async def unsubscribe(self, symbols: list[str]) -> None:
        """Unsubscribe from symbols on the provider connection."""
        websocket = self._require_websocket()
        await websocket.send(
            json.dumps(
                {
                    "action": "unsubscribe",
                    "params": {"symbols": ",".join(symbols)},
                }
            )
        )

    async def receive(self) -> list[PriceUpdate]:
        """Parse one Twelve Data price message."""
        websocket = self._require_websocket()
        message = json.loads(await websocket.recv())
        if message.get("event") != "price" or not message.get("symbol"):
            return []
        timestamp = message.get("timestamp") or message.get("time")
        return [
            PriceUpdate(
                symbol=str(message["symbol"]),
                price=Decimal(str(message["price"])),
                timestamp=datetime.fromtimestamp(
                    float(timestamp), tz=timezone.utc
                ),
            )
        ]

    async def disconnect(self) -> None:
        """Close the provider connection."""
        if self.websocket is not None:
            await self.websocket.close()
            self.websocket = None


class FinnhubStream(MarketDataStream):
    """Backend-owned Finnhub trade WebSocket adapter."""

    url = "wss://ws.finnhub.io"

    def __init__(self, api_key: str, websocket=None) -> None:
        """Create a stream with an optional injected WebSocket test double."""
        self.api_key = api_key
        self.websocket = websocket

    def _require_websocket(self) -> Any:
        """Return the connected socket or raise a clear lifecycle error."""
        if self.websocket is None:
            raise RuntimeError("Finnhub stream is not connected")
        return self.websocket

    async def connect(self) -> None:
        """Open the Finnhub WebSocket when one was not injected."""
        if self.websocket is None:
            self.websocket = await websockets.connect(
                f"{self.url}?token={self.api_key}"
            )

    async def subscribe(self, symbols: list[str]) -> None:
        """Subscribe to each Finnhub trade symbol."""
        websocket = self._require_websocket()
        for symbol in symbols:
            await websocket.send(
                json.dumps({"type": "subscribe", "symbol": symbol})
            )

    async def unsubscribe(self, symbols: list[str]) -> None:
        """Unsubscribe from each Finnhub trade symbol."""
        websocket = self._require_websocket()
        for symbol in symbols:
            await websocket.send(
                json.dumps({"type": "unsubscribe", "symbol": symbol})
            )

    async def receive(self) -> list[PriceUpdate]:
        """Parse one Finnhub trade message into price updates."""
        websocket = self._require_websocket()
        message = json.loads(await websocket.recv())
        if message.get("type") != "trade":
            return []
        return [
            PriceUpdate(
                symbol=str(item["s"]),
                price=Decimal(str(item["p"])),
                timestamp=datetime.fromtimestamp(
                    float(item["t"]) / 1000, tz=timezone.utc
                ),
            )
            for item in message.get("data", [])
            if item.get("s") and item.get("p") is not None and item.get("t")
        ]

    async def disconnect(self) -> None:
        """Close the provider connection."""
        if self.websocket is not None:
            await self.websocket.close()
            self.websocket = None
