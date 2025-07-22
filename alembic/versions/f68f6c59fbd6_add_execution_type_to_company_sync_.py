"""Add execution_type to company_sync_history

Revision ID: f68f6c59fbd6
Revises: 0db652fd27c7
Create Date: 2025-07-22 21:34:45.557881

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f68f6c59fbd6'
down_revision: Union[str, None] = '0db652fd27c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add execution_type column to company_sync_history table
    op.add_column('company_sync_history', 
        sa.Column('execution_type', sa.String(length=20), nullable=True, 
                  server_default='manual', comment='実行タイプ（manual/scheduled）')
    )


def downgrade() -> None:
    # Remove execution_type column from company_sync_history table
    op.drop_column('company_sync_history', 'execution_type')
