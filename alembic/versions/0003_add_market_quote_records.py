"""Copyright (c) 2026 TradeWare contributors.

Add persisted market quote snapshots.
"""

import sqlalchemy as sa

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the market quote history table."""
    op.create_table(
        "market_quote_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("price", sa.Numeric(18, 6), nullable=False),
        sa.Column("open", sa.Numeric(18, 6)),
        sa.Column("high", sa.Numeric(18, 6)),
        sa.Column("low", sa.Numeric(18, 6)),
        sa.Column("previous_close", sa.Numeric(18, 6)),
        sa.Column("change", sa.Numeric(18, 6)),
        sa.Column("change_percent", sa.Numeric(18, 6)),
        sa.Column("provider_timestamp", sa.DateTime(timezone=True)),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_market_quote_records_id", "market_quote_records", ["id"])
    op.create_index(
        "ix_market_quote_records_symbol", "market_quote_records", ["symbol"]
    )


def downgrade() -> None:
    """Remove the market quote history table."""
    op.drop_index("ix_market_quote_records_symbol", table_name="market_quote_records")
    op.drop_index("ix_market_quote_records_id", table_name="market_quote_records")
    op.drop_table("market_quote_records")
