"""Copyright (c) 2026 TradeWare contributors.

Add the database-backed stock universe.
"""

import sqlalchemy as sa

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the stocks table."""
    op.create_table(
        "stocks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("exchange", sa.String(length=64), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("asset_type", sa.String(length=32), nullable=False),
        sa.Column(
            "is_active", sa.Boolean(), server_default=sa.true(), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("symbol"),
    )
    op.create_index("ix_stocks_id", "stocks", ["id"])
    op.create_index("ix_stocks_symbol", "stocks", ["symbol"])


def downgrade() -> None:
    """Remove the stocks table."""
    op.drop_index("ix_stocks_symbol", table_name="stocks")
    op.drop_index("ix_stocks_id", table_name="stocks")
    op.drop_table("stocks")
