from fastapi import APIRouter

from trade_ware.core.security import CurrentUser, DbSession
from trade_ware.schemas.profile import ProfileUpdate, UserProfileResponse
from trade_ware.services.profile_service import ProfileService

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/me", response_model=UserProfileResponse)
def get_current_user_profile(
    db: DbSession, current_user: CurrentUser
) -> UserProfileResponse:
    return ProfileService.get_profile(db, current_user)


@router.patch("/me/profile", response_model=UserProfileResponse)
def update_current_user_profile(
    payload: ProfileUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> UserProfileResponse:
    return ProfileService.update_profile(db, current_user, payload)
