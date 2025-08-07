"""Remove trades_spec weekly_margin_interest and announcement tables

Revision ID: 0bd55ee18e0a
Revises: da6b106853ae
Create Date: 2025-08-07 15:49:05.989610

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0bd55ee18e0a"
down_revision: Union[str, None] = "da6b106853ae"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop tables
    op.drop_table("trades_spec")
    op.drop_table("weekly_margin_interest")
    op.drop_table("announcements")


def downgrade() -> None:
    """Downgrade schema."""
    # Re-create announcements table
    op.create_table(
        "announcements",
        sa.Column("date", sa.Date(), nullable=False, comment="発表日"),
        sa.Column("code", sa.String(length=5), nullable=False, comment="銘柄コード"),
        sa.Column("fiscal_quarter", sa.String(length=50), nullable=False, comment="四半期区分"),
        sa.Column("company_name", sa.String(length=255), nullable=False, comment="会社名"),
        sa.Column("fiscal_year", sa.String(length=10), nullable=False, comment="決算期"),
        sa.Column("sector_name", sa.String(length=100), nullable=False, comment="業種名"),
        sa.Column("section", sa.String(length=50), nullable=False, comment="市場区分"),
        sa.PrimaryKeyConstraint("date", "code", "fiscal_quarter"),
        sa.UniqueConstraint("date", "code", "fiscal_quarter", name="uq_announcement"),
    )
    op.create_index(op.f("ix_announcements_code"), "announcements", ["code"], unique=False)
    op.create_index(op.f("ix_announcements_date"), "announcements", ["date"], unique=False)
    
    # Re-create weekly_margin_interests table
    op.create_table(
        "weekly_margin_interest",
        sa.Column("code", sa.String(length=10), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("short_margin_trade_volume", sa.Float(), nullable=True),
        sa.Column("long_margin_trade_volume", sa.Float(), nullable=True),
        sa.Column("short_negotiable_margin_trade_volume", sa.Float(), nullable=True),
        sa.Column("long_negotiable_margin_trade_volume", sa.Float(), nullable=True),
        sa.Column("short_standardized_margin_trade_volume", sa.Float(), nullable=True),
        sa.Column("long_standardized_margin_trade_volume", sa.Float(), nullable=True),
        sa.Column("issue_type", sa.String(length=1), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("code", "date"),
    )
    op.create_index("idx_weekly_margin_interest_code", "weekly_margin_interest", ["code"], unique=False)
    op.create_index("idx_weekly_margin_interest_date", "weekly_margin_interest", ["date"], unique=False)
    op.create_index("idx_weekly_margin_interest_date_issue_type", "weekly_margin_interest", ["date", "issue_type"], unique=False)
    op.create_index("idx_weekly_margin_interest_issue_type", "weekly_margin_interest", ["issue_type"], unique=False)
    
    # Re-create trades_spec table
    op.create_table(
        "trades_spec",
        sa.Column("code", sa.String(10), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("section", sa.String(50), nullable=True),
        sa.Column("sales_proprietary", sa.BigInteger(), nullable=True),
        sa.Column("purchases_proprietary", sa.BigInteger(), nullable=True),
        sa.Column("balance_proprietary", sa.BigInteger(), nullable=True),
        sa.Column("sales_consignment_individual", sa.BigInteger(), nullable=True),
        sa.Column("purchases_consignment_individual", sa.BigInteger(), nullable=True),
        sa.Column("balance_consignment_individual", sa.BigInteger(), nullable=True),
        sa.Column("sales_consignment_corporate", sa.BigInteger(), nullable=True),
        sa.Column("purchases_consignment_corporate", sa.BigInteger(), nullable=True),
        sa.Column("balance_consignment_corporate", sa.BigInteger(), nullable=True),
        sa.Column("sales_consignment_investment_trust", sa.BigInteger(), nullable=True),
        sa.Column("purchases_consignment_investment_trust", sa.BigInteger(), nullable=True),
        sa.Column("balance_consignment_investment_trust", sa.BigInteger(), nullable=True),
        sa.Column("sales_consignment_foreign", sa.BigInteger(), nullable=True),
        sa.Column("purchases_consignment_foreign", sa.BigInteger(), nullable=True),
        sa.Column("balance_consignment_foreign", sa.BigInteger(), nullable=True),
        sa.Column("sales_consignment_other_corporate", sa.BigInteger(), nullable=True),
        sa.Column("purchases_consignment_other_corporate", sa.BigInteger(), nullable=True),
        sa.Column("balance_consignment_other_corporate", sa.BigInteger(), nullable=True),
        sa.Column("sales_consignment_other", sa.BigInteger(), nullable=True),
        sa.Column("purchases_consignment_other", sa.BigInteger(), nullable=True),
        sa.Column("balance_consignment_other", sa.BigInteger(), nullable=True),
        sa.Column("sales_total", sa.BigInteger(), nullable=True),
        sa.Column("purchases_total", sa.BigInteger(), nullable=True),
        sa.Column("balance_total", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("code", "trade_date")
    )
    op.create_index("idx_trades_spec_code", "trades_spec", ["code"])
    op.create_index("idx_trades_spec_date", "trades_spec", ["trade_date"])
    op.create_index("idx_trades_spec_section", "trades_spec", ["section"])
    op.create_index("idx_trades_spec_date_section", "trades_spec", ["trade_date", "section"])
