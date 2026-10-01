"""Protected client endpoints for backend-stored market data."""

from fastapi import APIRouter, HTTPException, Query, status

from trade_ware.core.security import CurrentUser
from trade_ware.market_data.dependencies import get_market_data_service
from trade_ware.market_data.exceptions import StaleMarketDataError
from trade_ware.schemas.market_data import (
    HistoricalPriceResponse,
    LatestPriceResponse,
)

router = APIRouter(prefix="/api/v1/market-data", tags=["market-data"])


@router.get("/price/{symbol}", response_model=LatestPriceResponse)
async def get_latest_price(
    symbol: str, current_user: CurrentUser
) -> LatestPriceResponse:
    """Return a latest price from Redis without calling a provider."""
    try:
        update = await get_market_data_service().get_latest_price(symbol)
    except StaleMarketDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return LatestPriceResponse(
        symbol=update.symbol,
        price=update.price,
        timestamp=update.timestamp,
    )


@router.get("/history/{symbol}", response_model=list[HistoricalPriceResponse])
async def get_price_history(
    symbol: str,
    current_user: CurrentUser,
    limit: int = Query(default=100, ge=1, le=1000),
) -> list[HistoricalPriceResponse]:
    """Return persisted quote snapshots from PostgreSQL."""
    history = await get_market_data_service().get_history(symbol, limit)
    return [
        HistoricalPriceResponse(
            symbol=item.symbol,
            timestamp=item.timestamp,
            open=item.open,
            high=item.high,
            low=item.low,
            close=item.close,
            volume=item.volume,
        )
        for item in history
    ]
