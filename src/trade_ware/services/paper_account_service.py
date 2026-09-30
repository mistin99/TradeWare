"""Copyright (c) 2026 TradeWare contributors.

Services for creating, retrieving, and resetting simulated cash accounts.
"""

from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from trade_ware.core.config import settings
from trade_ware.models.paper_account import PaperAccount
from trade_ware.models.user import User


class PaperAccountService:
    """Manage the authenticated user's simulated cash account."""

    @staticmethod
    def get_account(db: Session, user: User) -> PaperAccount | None:
        """Return the user's account, or ``None`` when it does not exist."""
        return (
            db.query(PaperAccount)
            .filter(PaperAccount.user_id == user.id)
            .first()
        )

    @staticmethod
    def create_account(db: Session, user: User) -> PaperAccount:
        """Create and persist a new account with the configured balance."""
        account = PaperAccount(
            user_id=user.id,
            cash_balance=Decimal(settings.paper_account_starting_balance),
        )
        db.add(account)
        db.commit()
        db.refresh(account)
        return account

    @staticmethod
    def get_or_create(db: Session, user: User) -> PaperAccount:
        """Return the user's account, creating it when it is absent."""
        account = PaperAccountService.get_account(db, user)
        if account:
            return account

        try:
            return PaperAccountService.create_account(db, user)
        except IntegrityError:
            db.rollback()
            account = PaperAccountService.get_account(db, user)
            if account:
                return account
            raise

    @staticmethod
    def reset_balance(db: Session, user: User) -> PaperAccount:
        """Restore the user's cash balance.

        The configured starting amount is used as the reset value.
        """
        account = PaperAccountService.get_account(db, user)
        if not account:
            return PaperAccountService.create_account(db, user)

        account.cash_balance = Decimal(settings.paper_account_starting_balance)
        db.commit()
        db.refresh(account)
        return account
