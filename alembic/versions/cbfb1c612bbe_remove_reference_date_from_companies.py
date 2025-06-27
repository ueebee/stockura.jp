"""remove_reference_date_from_companies

Revision ID: cbfb1c612bbe
Revises: 196afdc25a27
Create Date: 2025-06-27 00:42:58.591787

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cbfb1c612bbe'
down_revision: Union[str, None] = '196afdc25a27'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # reference_dateインデックスを削除
    op.drop_index('ix_companies_code_date', table_name='companies')
    
    # reference_dateカラムを削除
    op.drop_column('companies', 'reference_date')


def downgrade() -> None:
    # reference_dateカラムを追加
    op.add_column('companies', sa.Column('reference_date', sa.Date(), nullable=False, server_default='2025-06-27'))
    
    # reference_dateインデックスを追加
    op.create_index('ix_companies_code_date', 'companies', ['code', 'reference_date'])
