import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from trade_ware.core.config import settings
from trade_ware.models.email_verification_token import EmailVerificationToken
from trade_ware.models.user import User
from trade_ware.schemas.user import (
    EmailVerificationResponse,
    UserCreate,
    UserRegisterResponse,
)
from trade_ware.services.email_service import EmailService

EMAIL_VERIFICATION_TOKEN_TTL = timedelta(minutes=15)


class UserAuthService:
    """Handles user registration and email verification use cases."""

    @staticmethod
    def hash_password(password: str) -> str:
        salt = secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100_000,
        )
        return f"pbkdf2_sha256${salt}${digest.hex()}"

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        if not password_hash.startswith("pbkdf2_sha256$"):
            return False

        _, salt, digest_hex = password_hash.split("$", 2)
        derived = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100_000,
        )
        return derived.hex() == digest_hex

    @classmethod
    def register_user(cls, db: Session, payload: UserCreate) -> UserRegisterResponse:
        normalized_email = payload.email.lower()
        existing_user = db.query(User).filter(User.email == normalized_email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        cls._delete_expired_verification_tokens(db)

        user = User(
            email=normalized_email,
            password_hash=cls.hash_password(payload.password),
            is_verified=False,
        )
        db.add(user)
        db.flush()

        verification_token = secrets.token_urlsafe(32)
        db.query(EmailVerificationToken).filter(
            EmailVerificationToken.user_id == user.id
        ).delete()
        db.add(
            EmailVerificationToken(
                user_id=user.id,
                token=verification_token,
            )
        )
        db.commit()
        db.refresh(user)

        verification_url = f"{settings.app_base_url.rstrip('/')}/api/v1/auth/verify-email?token={verification_token}"
        body = (
            "Welcome to TradeWare!\n\n"
            "Please verify your email by visiting the link below:\n\n"
            f"{verification_url}\n\n"
            "If you did not create this account, you can ignore this email."
        )
        html_body = (
            "<html><body>"
            "<h2>Welcome to TradeWare</h2>"
            "<p>Please verify your email by clicking the link below:</p>"
            f"<p><a href='{verification_url}'>Verify your email</a></p>"
            "<p>If you did not create this account, you can ignore this email.</p>"
            "</body></html>"
        )

        EmailService.send_email(
            user.email,
            "Verify your TradeWare account",
            body,
            html_body=html_body,
        )

        return UserRegisterResponse(
            id=user.id,
            email=user.email,
            is_verified=user.is_verified,
            verification_url=verification_url,
        )

    @classmethod
    def verify_email(cls, db: Session, token: str) -> EmailVerificationResponse:
        record = (
            db.query(EmailVerificationToken)
            .filter(EmailVerificationToken.token == token)
            .first()
        )
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid verification token",
            )

        created_at = record.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        expires_at = created_at + EMAIL_VERIFICATION_TOKEN_TTL
        if datetime.now(timezone.utc) >= expires_at:
            db.delete(record)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Verification token has expired",
            )

        user = db.query(User).filter(User.id == record.user_id).first()
        if not user:
            db.delete(record)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found for verification token",
            )

        user.is_verified = True
        db.delete(record)
        db.commit()

        return EmailVerificationResponse(
            email=user.email,
            message="Email verified successfully. You can now log in to TradeWare.",
        )

    @staticmethod
    def _delete_expired_verification_tokens(db: Session) -> None:
        """Remove expired tokens during registration."""
        cutoff = datetime.now(timezone.utc) - EMAIL_VERIFICATION_TOKEN_TTL
        db.query(EmailVerificationToken).filter(
            EmailVerificationToken.created_at <= cutoff
        ).delete(synchronize_session=False)
