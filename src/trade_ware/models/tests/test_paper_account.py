"""Copyright (c) 2026 TradeWare contributors.

Unit tests for the simulated cash-account SQLAlchemy model.
"""

from decimal import Decimal

from trade_ware.models.paper_account import PaperAccount


def test_paper_account_model_has_virtual_cash_and_unique_owner():
    """Verify cash precision and one-account-per-user constraints."""
    account = PaperAccount(user_id=4, cash_balance=Decimal("100000.00"))
    columns = PaperAccount.__table__.columns

    assert PaperAccount.__tablename__ == "paper_accounts"
    assert account.cash_balance == Decimal("100000.00")
    assert columns["user_id"].unique
    assert columns["cash_balance"].nullable is False
    assert columns["cash_balance"].type.precision == 14
    assert columns["cash_balance"].type.scale == 2
