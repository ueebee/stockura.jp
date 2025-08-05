"""Add trades_spec table for investment department trading data

Revision ID: e1a2b3c4d5e6
Revises: dba980847750
Create Date: 2025-08-05 00:50:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e1a2b3c4d5e6"
down_revision: Union[str, None] = "dba980847750"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create trades_spec table"""
    op.create_table(
        "trades_spec",
        sa.Column("code", sa.String(10), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("section", sa.String(50), nullable=True),
        
        # 自己勘定（証券会社）
        sa.Column("sales_proprietary", sa.Integer(), nullable=True),
        sa.Column("purchases_proprietary", sa.Integer(), nullable=True),
        sa.Column("balance_proprietary", sa.Integer(), nullable=True),
        
        # 委託（個人）
        sa.Column("sales_consignment_individual", sa.Integer(), nullable=True),
        sa.Column("purchases_consignment_individual", sa.Integer(), nullable=True),
        sa.Column("balance_consignment_individual", sa.Integer(), nullable=True),
        
        # 委託（法人）
        sa.Column("sales_consignment_corporate", sa.Integer(), nullable=True),
        sa.Column("purchases_consignment_corporate", sa.Integer(), nullable=True),
        sa.Column("balance_consignment_corporate", sa.Integer(), nullable=True),
        
        # 委託（投資信託）
        sa.Column("sales_consignment_investment_trust", sa.Integer(), nullable=True),
        sa.Column("purchases_consignment_investment_trust", sa.Integer(), nullable=True),
        sa.Column("balance_consignment_investment_trust", sa.Integer(), nullable=True),
        
        # 委託（外国人）
        sa.Column("sales_consignment_foreign", sa.Integer(), nullable=True),
        sa.Column("purchases_consignment_foreign", sa.Integer(), nullable=True),
        sa.Column("balance_consignment_foreign", sa.Integer(), nullable=True),
        
        # 委託（その他法人）
        sa.Column("sales_consignment_other_corporate", sa.Integer(), nullable=True),
        sa.Column("purchases_consignment_other_corporate", sa.Integer(), nullable=True),
        sa.Column("balance_consignment_other_corporate", sa.Integer(), nullable=True),
        
        # 委託（その他）
        sa.Column("sales_consignment_other", sa.Integer(), nullable=True),
        sa.Column("purchases_consignment_other", sa.Integer(), nullable=True),
        sa.Column("balance_consignment_other", sa.Integer(), nullable=True),
        
        # 合計
        sa.Column("sales_total", sa.Integer(), nullable=True),
        sa.Column("purchases_total", sa.Integer(), nullable=True),
        sa.Column("balance_total", sa.Integer(), nullable=True),
        
        # タイムスタンプ
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        
        # 主キー
        sa.PrimaryKeyConstraint("code", "trade_date")
    )
    
    # インデックス作成
    op.create_index("idx_trades_spec_code", "trades_spec", ["code"])
    op.create_index("idx_trades_spec_date", "trades_spec", ["trade_date"])
    op.create_index("idx_trades_spec_section", "trades_spec", ["section"])
    op.create_index("idx_trades_spec_date_section", "trades_spec", ["trade_date", "section"])


def downgrade() -> None:
    """Drop trades_spec table"""
    # インデックス削除
    op.drop_index("idx_trades_spec_date_section", table_name="trades_spec")
    op.drop_index("idx_trades_spec_section", table_name="trades_spec")
    op.drop_index("idx_trades_spec_date", table_name="trades_spec")
    op.drop_index("idx_trades_spec_code", table_name="trades_spec")
    
    # テーブル削除
    op.drop_table("trades_spec")