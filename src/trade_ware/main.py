from contextlib import asynccontextmanager

from fastapi import FastAPI

from trade_ware.api.auth import router as auth_router
from trade_ware.api.market_data import router as market_data_router
from trade_ware.api.paper_account import router as paper_account_router
from trade_ware.api.users import router as users_router
from trade_ware.core.config import settings
from trade_ware.market_data.worker import MarketDataRefreshWorker

worker = MarketDataRefreshWorker()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start and stop the backend market-data refresh worker."""
    worker.start()
    try:
        yield
    finally:
        await worker.stop()


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(paper_account_router)
app.include_router(market_data_router)


@app.get("/")
async def root():
    """Root endpoint of the app."""
    return {"message": "Welcome to TradeWare"}
