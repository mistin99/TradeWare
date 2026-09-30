from trade_ware.models.email_verification_token import EmailVerificationToken


def test_verification_token_model_maps_expected_columns():
    columns = EmailVerificationToken.__table__.columns

    assert EmailVerificationToken.__tablename__ == "email_verification_tokens"
    assert columns["id"].primary_key
    assert columns["user_id"].unique
    assert columns["user_id"].nullable is False
    foreign_key = next(iter(columns["user_id"].foreign_keys))
    assert foreign_key.target_fullname == "users.id"
    assert columns["token"].unique
    assert columns["token"].nullable is False


def test_verification_token_model_accepts_token_fields():
    token = EmailVerificationToken(user_id=3, token="one-time-token")

    assert token.user_id == 3
    assert token.token == "one-time-token"

