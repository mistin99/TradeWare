"""Configuration-based construction of market-data provider strategies."""

import httpx

from trade_ware.core.config import Settings
from trade_ware.market_data.exceptions import MarketDataError
from trade_ware.market_data.provider import MarketDataProvider
from trade_ware.market_data.providers.finnhub import FinnhubProvider
from trade_ware.market_data.providers.twelve_data import TwelveDataProvider


class MarketDataProviderFactory:
    """Build the configured concrete provider without leaking selection logic."""

    @staticmethod
    def create(
        settings: Settings,
        client: httpx.AsyncClient | None = None,
    ) -> MarketDataProvider:
        """Create the configured provider strategy."""
        provider = settings.market_data_provider.lower()
        if provider == "twelve_data":
            if not settings.twelve_data_api_key:
                raise MarketDataError("TWELVE_DATA_API_KEY is not configured")
            return TwelveDataProvider(
                settings.twelve_data_api_key,
                client,
                settings.market_data_timeout_seconds,
            )
        if provider == "finnhub":
            if not settings.finnhub_api_key:
                raise MarketDataError("FINNHUB_API_KEY is not configured")
            return FinnhubProvider(
                settings.finnhub_api_key,
                client,
                settings.market_data_timeout_seconds,
            )
        raise MarketDataError(f"Unsupported market-data provider: {provider}")
