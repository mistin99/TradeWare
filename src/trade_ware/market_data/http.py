"""Shared HTTP response and parsing helpers for market-data providers."""

import logging
from collections.abc import Mapping
from typing import Any

import httpx

from trade_ware.market_data.exceptions import (
    InvalidSymbolError,
    ProviderUnavailableError,
)

logger = logging.getLogger(__name__)


async def request_json(
    client: httpx.AsyncClient,
    provider: str,
    operation: str,
    url: str,
    params: Mapping[str, Any],
) -> dict[str, Any] | list[Any]:
    """Request JSON without exposing provider-specific errors to callers."""
    try:
        response = await client.get(url, params=params)
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning(
            "Market-data request failed provider=%s operation=%s", provider, operation
        )
        raise ProviderUnavailableError(f"{provider} failed during {operation}") from exc

    if isinstance(payload, dict) and (
        payload.get("status") == "error" or payload.get("code")
    ):
        message = str(
            payload.get("message") or payload.get("error") or "provider error"
        )
        raise InvalidSymbolError(message)
    if not isinstance(payload, (dict, list)):
        raise ProviderUnavailableError(f"{provider} returned malformed JSON")
    return payload
