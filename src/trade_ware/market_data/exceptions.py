"""Application exceptions raised by the market-data integration layer."""


class MarketDataError(Exception):
    """Base error for expected market-data failures."""


class ProviderUnavailableError(MarketDataError):
    """The selected provider could not serve a request."""


class InvalidSymbolError(MarketDataError):
    """The provider rejected a symbol or returned no usable data."""


class UnsupportedMarketDataError(MarketDataError):
    """The selected provider does not support an operation."""


class StaleMarketDataError(MarketDataError):
    """No sufficiently fresh price is available in the local cache."""
