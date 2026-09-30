from unittest.mock import Mock, patch

from trade_ware.api.auth import register_user, verify_email
from trade_ware.schemas.user import (
    EmailVerificationResponse,
    UserCreate,
    UserRegisterResponse,
)
from trade_ware.services.user_auth_service import UserAuthService


def test_register_user_delegates_to_service():
    db = Mock()
    payload = UserCreate(email="person@example.com", password="StrongPass123!")
    expected = UserRegisterResponse(
        id=7,
        email="person@example.com",
        is_verified=False,
        verification_url="http://localhost/verify?token=abc",
    )
    with patch.object(
        UserAuthService, "register_user", return_value=expected
    ) as register_mock:
        result = register_user(payload, db)

    assert result == expected
    register_mock.assert_called_once_with(db, payload)


def test_verify_email_delegates_to_service():
    db = Mock()
    expected = EmailVerificationResponse(
        email="person@example.com", message="Email verified successfully"
    )
    with patch.object(
        UserAuthService, "verify_email", return_value=expected
    ) as verify_mock:
        result = verify_email("verification-token", db)

    assert result == expected
    verify_mock.assert_called_once_with(db, "verification-token")

