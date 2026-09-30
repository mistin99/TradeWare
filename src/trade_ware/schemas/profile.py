from pydantic import BaseModel, ConfigDict, Field


class ProfileUpdate(BaseModel):
    """Allowed personal information for profile onboarding."""

    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)


class UserProfileResponse(BaseModel):
    """Current account and onboarding state."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    is_verified: bool
    profile_completed: bool
    first_name: str | None
    last_name: str | None
