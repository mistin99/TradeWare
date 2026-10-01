"""Background job that refreshes configured market quotes every 60 seconds."""

import asyncio
import logging

from trade_ware.core.config import settings
from trade_ware.market_data.dependencies import get_market_data_service

logger = logging.getLogger(__name__)


class MarketDataRefreshWorker:
    """Refresh configured symbols through the injected market-data service."""

    def __init__(self) -> None:
        """Create a worker using application settings."""
        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()

    def start(self) -> None:
        """Start one background refresh task."""
        if self._task is None:
            self._task = asyncio.create_task(self.run())

    async def stop(self) -> None:
        """Stop the refresh task and wait for it to finish."""
        self._stop_event.set()
        if self._task:
            await self._task
            self._task = None

    async def run(self) -> None:
        """Refresh all configured symbols at a fixed interval."""
        service = get_market_data_service()
        while not self._stop_event.is_set():
            symbols = await service.refresh_symbol_universe()
            for symbol in symbols:
                try:
                    await service.refresh_quote(symbol)
                except Exception:
                    logger.exception(
                        "Market quote refresh failed symbol=%s", symbol
                    )
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=settings.market_data_refresh_interval_seconds,
                )
            except asyncio.TimeoutError:
                continue
