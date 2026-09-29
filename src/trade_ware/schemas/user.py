from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Payload used when creating a new user account."""

    email: EmailStr
    password: str = Field(..., min_length=8)


class UserRead(BaseModel):
    """Public user representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    is_verified: bool


class UserRegisterResponse(UserRead):
    """Registration response with verification guidance."""

    verification_url: str


class EmailVerificationResponse(BaseModel):
    """Response returned after successful email verification."""

    email: EmailStr
    message: str
