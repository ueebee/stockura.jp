"""add_api_endpoint_schedules_table

Revision ID: 999d813c6d1c
Revises: a44b1331d4ce
Create Date: 2025-07-10 16:56:30.513661

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '999d813c6d1c'
down_revision: Union[str, None] = 'a44b1331d4ce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create api_endpoint_schedules table
    op.create_table(
        'api_endpoint_schedules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('endpoint_id', sa.Integer(), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('schedule_type', sa.String(20), nullable=False, server_default='daily'),
        sa.Column('execution_time', sa.Time(), nullable=False, server_default='05:00:00'),
        sa.Column('timezone', sa.String(50), nullable=False, server_default='Asia/Tokyo'),
        sa.Column('last_execution_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_execution_status', sa.String(20), nullable=True),
        sa.Column('last_sync_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['endpoint_id'], ['api_endpoints.id'], ),
        sa.UniqueConstraint('endpoint_id')
    )
    
    # Create index
    op.create_index('ix_api_endpoint_schedules_endpoint_id', 'api_endpoint_schedules', ['endpoint_id'])
    
    # Insert default schedule for listed companies endpoint
    op.execute("""
        INSERT INTO api_endpoint_schedules (endpoint_id, is_enabled, schedule_type, execution_time, timezone, created_at, updated_at)
        SELECT id, true, 'daily', '05:00:00', 'Asia/Tokyo', NOW(), NOW()
        FROM api_endpoints
        WHERE data_type = 'listed_companies'
        LIMIT 1
    """)


def downgrade() -> None:
    op.drop_index('ix_api_endpoint_schedules_endpoint_id', table_name='api_endpoint_schedules')
    op.drop_table('api_endpoint_schedules')
