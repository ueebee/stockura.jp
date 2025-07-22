"""Add execution_type to daily_quotes_sync_history

Revision ID: 0db652fd27c7
Revises: ed29ac7c0594
Create Date: 2025-07-22 19:56:32.626113

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0db652fd27c7'
down_revision: Union[str, None] = 'ed29ac7c0594'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add execution_type column to daily_quotes_sync_history table
    op.add_column('daily_quotes_sync_history', 
        sa.Column('execution_type', sa.String(length=20), nullable=True, 
                  server_default='manual', comment='実行タイプ（manual/scheduled）')
    )


def downgrade() -> None:
    # Remove execution_type column from daily_quotes_sync_history table
    op.drop_column('daily_quotes_sync_history', 'execution_type')
