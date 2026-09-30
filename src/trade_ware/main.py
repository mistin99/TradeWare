"""Main entry point of the application."""

from fastapi import FastAPI

from trade_ware.api.auth import router as auth_router
from trade_ware.api.paper_account import router as paper_account_router
from trade_ware.api.users import router as users_router
from trade_ware.core.config import settings

app = FastAPI(title=settings.app_name)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(paper_account_router)


@app.get("/")
async def root():
    """Root endpoint of the app."""
    return {"message": "Welcome to TradeWare"}
