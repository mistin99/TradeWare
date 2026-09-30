from unittest.mock import Mock, patch

from trade_ware.api.users import get_current_user_profile, update_current_user_profile
from trade_ware.models.user import User
from trade_ware.schemas.profile import ProfileUpdate, UserProfileResponse


def test_get_current_user_profile_delegates_to_service():
    db = Mock()
    user = User(id=1, email="person@example.com", password_hash="hashed")
    expected = UserProfileResponse(
        id=1,
        email="person@example.com",
        is_verified=True,
        profile_completed=False,
        first_name=None,
        last_name=None,
    )
    with patch(
        "trade_ware.api.users.ProfileService.get_profile",
        return_value=expected,
    ) as service_mock:
        result = get_current_user_profile(db, user)

    assert result == expected
    service_mock.assert_called_once_with(db, user)


def test_update_current_user_profile_delegates_to_service():
    db = Mock()
    user = User(id=1, email="person@example.com", password_hash="hashed")
    payload = ProfileUpdate(first_name="Ada")
    expected = UserProfileResponse(
        id=1,
        email="person@example.com",
        is_verified=True,
        profile_completed=False,
        first_name="Ada",
        last_name=None,
    )
    with patch(
        "trade_ware.api.users.ProfileService.update_profile",
        return_value=expected,
    ) as service_mock:
        result = update_current_user_profile(payload, db, user)

    assert result == expected
    service_mock.assert_called_once_with(db, user, payload)
