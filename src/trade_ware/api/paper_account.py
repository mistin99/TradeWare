"""Copyright (c) 2026 TradeWare contributors.

HTTP endpoints for the authenticated user's simulated cash account.
"""

from fastapi import APIRouter

from trade_ware.core.security import CurrentUser, DbSession
from trade_ware.schemas.paper_account import PaperAccountResponse
from trade_ware.services.paper_account_service import PaperAccountService

router = APIRouter(prefix="/api/v1/users", tags=["paper-account"])


@router.get("/me/paper-account", response_model=PaperAccountResponse)
def get_paper_account(
    db: DbSession, current_user: CurrentUser
) -> PaperAccountResponse:
    """Return or initialize the current user's paper account."""
    account = PaperAccountService.get_or_create(db, current_user)
    return PaperAccountResponse.model_validate(account)


@router.post("/me/paper-account/reset", response_model=PaperAccountResponse)
def reset_paper_account_balance(
    db: DbSession, current_user: CurrentUser
) -> PaperAccountResponse:
    """Reset the current user's virtual cash to its starting balance."""
    account = PaperAccountService.reset_balance(db, current_user)
    return PaperAccountResponse.model_validate(account)
