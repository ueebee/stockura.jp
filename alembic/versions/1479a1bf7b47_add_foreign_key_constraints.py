"""add_foreign_key_constraints

Revision ID: 1479a1bf7b47
Revises: 8aff57aa15b6
Create Date: 2025-06-26 10:09:17.742255

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1479a1bf7b47'
down_revision: Union[str, None] = '8aff57aa15b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 企業テーブルに外部キー制約を追加
    
    # 市場コードの外部キー制約
    op.create_foreign_key(
        'fk_companies_market_code',
        'companies', 'market_masters',
        ['market_code'], ['code'],
        ondelete='SET NULL'  # マスターデータ削除時はNULLに設定
    )
    
    # 17業種コードの外部キー制約
    op.create_foreign_key(
        'fk_companies_sector17_code',
        'companies', 'sector17_masters',
        ['sector17_code'], ['code'],
        ondelete='SET NULL'
    )
    
    # 33業種コードの外部キー制約
    op.create_foreign_key(
        'fk_companies_sector33_code',
        'companies', 'sector33_masters',
        ['sector33_code'], ['code'],
        ondelete='SET NULL'
    )
    
    # 33業種と17業種の関連制約
    op.create_foreign_key(
        'fk_sector33_sector17_code',
        'sector33_masters', 'sector17_masters',
        ['sector17_code'], ['code'],
        ondelete='RESTRICT'  # 17業種が参照されている場合は削除不可
    )


def downgrade() -> None:
    # 外部キー制約を削除
    op.drop_constraint('fk_sector33_sector17_code', 'sector33_masters', type_='foreignkey')
    op.drop_constraint('fk_companies_sector33_code', 'companies', type_='foreignkey')
    op.drop_constraint('fk_companies_sector17_code', 'companies', type_='foreignkey')
    op.drop_constraint('fk_companies_market_code', 'companies', type_='foreignkey')
