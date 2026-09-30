import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from trade_ware.database.base import Base
from trade_ware.models.email_verification_token import EmailVerificationToken
from trade_ware.models.user import User
from trade_ware.schemas.user import UserCreate
from trade_ware.services.user_auth_service import UserAuthService


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_password_hash_round_trip():
    password_hash = UserAuthService.hash_password("StrongPass123!")

    assert password_hash.startswith("pbkdf2_sha256$")
    assert UserAuthService.verify_password("StrongPass123!", password_hash)
    assert not UserAuthService.verify_password("wrong-password", password_hash)
    assert not UserAuthService.verify_password("password", "invalid-hash")


def test_register_user_persists_user_and_mocks_email(db_session):
    payload = UserCreate(email="Person@Example.com", password="StrongPass123!")

    with (
        patch(
            "trade_ware.services.user_auth_service.EmailService.send_email"
        ) as email_mock,
        patch(
            "trade_ware.services.user_auth_service.settings.app_base_url",
            "https://tradeware.example",
        ),
    ):
        result = UserAuthService.register_user(db_session, payload)

    user = db_session.query(User).one()
    token = db_session.query(EmailVerificationToken).one()
    assert result.email == "person@example.com"
    assert result.is_verified is False
    assert result.verification_url.startswith(
        "https://tradeware.example/api/v1/auth/verify-email?token="
    )
    assert token.user_id == user.id
    assert result.verification_url.endswith(token.token)
    assert UserAuthService.verify_password(
        "StrongPass123!", user.password_hash
    )
    email_mock.assert_called_once()
    recipient, subject, body = email_mock.call_args.args
    assert recipient == "person@example.com"
    assert subject == "Verify your TradeWare account"
    assert result.verification_url in body
    assert "html_body" in email_mock.call_args.kwargs


def test_register_user_rejects_duplicate_email(db_session):
    payload = UserCreate(email="person@example.com", password="StrongPass123!")

    with patch(
        "trade_ware.services.user_auth_service.EmailService.send_email"
    ) as email_mock:
        UserAuthService.register_user(db_session, payload)
        with pytest.raises(HTTPException) as error:
            UserAuthService.register_user(db_session, payload)

    assert error.value.status_code == 409
    email_mock.assert_called_once()


def test_verify_email_marks_user_and_deletes_token(db_session):
    payload = UserCreate(email="person@example.com", password="StrongPass123!")
    with patch(
        "trade_ware.services.user_auth_service.EmailService.send_email"
    ) as email_mock:
        UserAuthService.register_user(db_session, payload)
        token = db_session.query(EmailVerificationToken).one()
        result = UserAuthService.verify_email(db_session, token.token)

    user = db_session.query(User).one()
    assert result.email == "person@example.com"
    assert user.is_verified is True
    assert db_session.query(EmailVerificationToken).count() == 0
    email_mock.assert_called_once()


def test_verify_email_rejects_unknown_token(db_session):
    with pytest.raises(HTTPException) as error:
        UserAuthService.verify_email(db_session, "unknown-token")

    assert error.value.status_code == 404


def test_verify_email_rejects_and_deletes_expired_token(db_session):
    payload = UserCreate(email="person@example.com", password="StrongPass123!")
    with patch(
        "trade_ware.services.user_auth_service.EmailService.send_email"
    ):
        UserAuthService.register_user(db_session, payload)

    token = db_session.query(EmailVerificationToken).one()
    token.created_at = datetime.now(timezone.utc) - timedelta(minutes=16)
    db_session.commit()

    with pytest.raises(HTTPException) as error:
        UserAuthService.verify_email(db_session, token.token)

    assert error.value.status_code == 410
    assert db_session.query(EmailVerificationToken).count() == 0
    assert db_session.query(User).one().is_verified is False


def test_registration_purges_expired_tokens(db_session):
    first_payload = UserCreate(
        email="first@example.com", password="StrongPass123!"
    )
    second_payload = UserCreate(
        email="second@example.com", password="StrongPass123!"
    )
    with patch(
        "trade_ware.services.user_auth_service.EmailService.send_email"
    ):
        UserAuthService.register_user(db_session, first_payload)
        expired_token = db_session.query(EmailVerificationToken).one()
        expired_token.created_at = datetime.now(timezone.utc) - timedelta(minutes=16)
        db_session.commit()

        UserAuthService.register_user(db_session, second_payload)

    remaining_tokens = db_session.query(EmailVerificationToken).all()
    assert len(remaining_tokens) == 1
    assert remaining_tokens[0].user_id == 2

