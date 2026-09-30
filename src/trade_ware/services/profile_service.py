from sqlalchemy.orm import Session

from trade_ware.models.user import User
from trade_ware.models.user_profile import UserProfile
from trade_ware.schemas.profile import ProfileUpdate, UserProfileResponse


class ProfileService:
    """Handles optional profile onboarding for the authenticated user."""

    @staticmethod
    def get_profile(db: Session, user: User) -> UserProfileResponse:
        profile = (
            db.query(UserProfile)
            .filter(UserProfile.user_id == user.id)
            .first()
        )
        return ProfileService._response(user, profile)

    @staticmethod
    def update_profile(
        db: Session, user: User, payload: ProfileUpdate
    ) -> UserProfileResponse:
        profile = (
            db.query(UserProfile)
            .filter(UserProfile.user_id == user.id)
            .first()
        )
        if not profile:
            profile = UserProfile(user_id=user.id)
            db.add(profile)

        updates = payload.model_dump(exclude_unset=True)
        for field, value in updates.items():
            setattr(profile, field, value.strip() if value else value)

        db.commit()
        db.refresh(profile)
        return ProfileService._response(user, profile)

    @staticmethod
    def _response(
        user: User, profile: UserProfile | None
    ) -> UserProfileResponse:
        first_name = profile.first_name if profile else None
        last_name = profile.last_name if profile else None
        return UserProfileResponse(
            id=user.id,
            email=user.email,
            is_verified=user.is_verified,
            profile_completed=bool(first_name and last_name),
            first_name=first_name,
            last_name=last_name,
        )
