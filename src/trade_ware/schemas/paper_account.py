"""Copyright (c) 2026 TradeWare contributors.

Pydantic response schemas for simulated cash-account endpoints.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class PaperAccountResponse(BaseModel):
    """Represent the virtual cash account returned to its owner."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    cash_balance: Decimal
    created_at: datetime
    updated_at: datetime
