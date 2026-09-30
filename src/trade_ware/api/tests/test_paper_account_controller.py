"""Copyright (c) 2026 TradeWare contributors.

Unit tests for simulated cash-account HTTP controller delegation.
"""

from unittest.mock import Mock, patch

from trade_ware.api.paper_account import (
    get_paper_account,
    reset_paper_account_balance,
)
from trade_ware.models.user import User
from trade_ware.schemas.paper_account import PaperAccountResponse


def test_get_paper_account_delegates_to_service():
    """Verify the retrieval endpoint delegates to the account service."""
    db = Mock()
    user = User(id=1, email="person@example.com", password_hash="hashed")
    expected = PaperAccountResponse(
        id=3,
        cash_balance="100000.00",
        created_at="2026-09-30T12:00:00Z",
        updated_at="2026-09-30T12:00:00Z",
    )

    with patch(
        "trade_ware.api.paper_account.PaperAccountService.get_or_create",
        return_value=expected,
    ) as service_mock:
        result = get_paper_account(db, user)

    assert result == expected
    service_mock.assert_called_once_with(db, user)


def test_reset_paper_account_delegates_to_service():
    """Verify the reset endpoint delegates to the account service."""
    db = Mock()
    user = User(id=1, email="person@example.com", password_hash="hashed")
    expected = PaperAccountResponse(
        id=3,
        cash_balance="100000.00",
        created_at="2026-09-30T12:00:00Z",
        updated_at="2026-09-30T12:00:00Z",
    )

    with patch(
        "trade_ware.api.paper_account.PaperAccountService.reset_balance",
        return_value=expected,
    ) as service_mock:
        result = reset_paper_account_balance(db, user)

    assert result == expected
    service_mock.assert_called_once_with(db, user)
