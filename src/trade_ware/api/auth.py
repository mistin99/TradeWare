from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from trade_ware.database.session import get_db
from trade_ware.schemas.user import (
    EmailVerificationResponse,
    UserCreate,
    UserRegisterResponse,
)
from trade_ware.services.user_auth_service import UserAuthService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
db_dependency = Depends(get_db)


@router.post(
    "/register",
    response_model=UserRegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    payload: UserCreate,
    db: Session = db_dependency,
) -> UserRegisterResponse:
    return UserAuthService.register_user(db, payload)


@router.get("/verify-email", response_model=EmailVerificationResponse)
def verify_email(
    token: str = Query(..., description="Email verification token"),
    db: Session = db_dependency,
) -> EmailVerificationResponse:
    return UserAuthService.verify_email(db, token)
