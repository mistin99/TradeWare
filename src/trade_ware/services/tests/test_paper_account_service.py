"""Copyright (c) 2026 TradeWare contributors.

Unit tests for simulated cash-account service behavior.
"""

from decimal import Decimal
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from trade_ware.database.base import Base
from trade_ware.models.paper_account import PaperAccount
from trade_ware.models.user import User
from trade_ware.services.paper_account_service import PaperAccountService


@pytest.fixture
def db_session():
    """Provide an isolated in-memory database for each service test."""
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


@pytest.fixture
def user(db_session):
    """Provide a verified user who owns the test account."""
    user = User(
        email="person@example.com",
        password_hash="hashed",
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_get_or_create_creates_starting_balance(db_session, user):
    """Verify get-or-create initializes a missing account."""
    with patch(
        "trade_ware.services.paper_account_service.settings"
    ) as settings_mock:
        settings_mock.paper_account_starting_balance = "100000.00"
        result = PaperAccountService.get_or_create(db_session, user)

    account = db_session.query(PaperAccount).one()
    assert result.id == account.id
    assert result.cash_balance == Decimal("100000.00")
    assert account.user_id == user.id


def test_get_account_returns_none_when_account_is_missing(db_session, user):
    """Verify lookup does not create an account as a side effect."""
    assert PaperAccountService.get_account(db_session, user) is None
    assert db_session.query(PaperAccount).count() == 0


def test_create_account_persists_a_new_account(db_session, user):
    """Verify explicit creation persists one account for the user."""
    with patch(
        "trade_ware.services.paper_account_service.settings"
    ) as settings_mock:
        settings_mock.paper_account_starting_balance = "100000.00"
        account = PaperAccountService.create_account(db_session, user)

    assert account.id is not None
    assert PaperAccountService.get_account(db_session, user).id == account.id


def test_get_or_create_recovers_from_concurrent_creation(db_session, user):
    """Verify a unique-race reloads the account created by another request."""
    existing = PaperAccount(user_id=user.id, cash_balance=Decimal("100000.00"))
    integrity_error = IntegrityError("insert", {}, Exception("duplicate"))

    with (
        patch.object(
            PaperAccountService,
            "get_account",
            side_effect=[None, existing],
        ),
        patch.object(
            PaperAccountService,
            "create_account",
            side_effect=integrity_error,
        ),
    ):
        result = PaperAccountService.get_or_create(db_session, user)

    assert result is existing


def test_get_or_create_does_not_reset_existing_balance(db_session, user):
    """Verify get-or-create preserves an existing cash balance."""
    account = PaperAccount(
        user_id=user.id,
        cash_balance=Decimal("97500.25"),
    )
    db_session.add(account)
    db_session.commit()

    result = PaperAccountService.get_or_create(db_session, user)

    assert result.cash_balance == Decimal("97500.25")
    assert db_session.query(PaperAccount).count() == 1


def test_reset_balance_restores_starting_balance(db_session, user):
    """Verify reset restores the configured starting cash balance."""
    account = PaperAccount(
        user_id=user.id,
        cash_balance=Decimal("97500.25"),
    )
    db_session.add(account)
    db_session.commit()

    with patch(
        "trade_ware.services.paper_account_service.settings"
    ) as settings_mock:
        settings_mock.paper_account_starting_balance = "100000.00"
        result = PaperAccountService.reset_balance(db_session, user)

    assert result.cash_balance == Decimal("100000.00")
    assert db_session.query(PaperAccount).one().cash_balance == Decimal(
        "100000.00"
    )
