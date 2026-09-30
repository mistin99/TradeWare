from trade_ware.models.user import User


def test_user_model_maps_expected_columns():
    columns = User.__table__.columns

    assert User.__tablename__ == "users"
    assert columns["id"].primary_key
    assert columns["email"].unique
    assert columns["email"].nullable is False
    assert columns["password_hash"].nullable is False
    assert columns["is_verified"].nullable is False


def test_user_model_accepts_user_fields():
    user = User(
        email="person@example.com",
        password_hash="hashed-password",
        is_verified=False,
    )

    assert user.email == "person@example.com"
    assert user.password_hash == "hashed-password"
    assert user.is_verified is False


def test_user_model_keeps_verification_separate_from_profile_state():
    user = User(
        email="person@example.com",
        password_hash="hashed-password",
        is_verified=True,
    )

    assert user.is_verified is True
    assert not hasattr(user, "profile_completed")

