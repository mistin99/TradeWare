"""Main entry point of the application."""

from fastapi import FastAPI

from trade_ware.api.auth import router as auth_router
from trade_ware.core.config import settings
from trade_ware.database.session import initialize_database

app = FastAPI(title=settings.app_name)

app.include_router(auth_router)


@app.on_event("startup")
async def startup_event() -> None:
    """Create database tables for the app on startup."""
    initialize_database()


@app.get("/")
async def root():
    """Root endpoint of the app."""
    return {"message": "Welcome to TradeWare"}
