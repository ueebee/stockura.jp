"""Add daily quote schedules table

Revision ID: ed29ac7c0594
Revises: 999d813c6d1c
Create Date: 2025-07-17 22:22:21.368750

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ed29ac7c0594'
down_revision: Union[str, None] = '999d813c6d1c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create daily_quote_schedules table
    op.create_table('daily_quote_schedules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False, comment='スケジュール名'),
        sa.Column('description', sa.Text(), nullable=True, comment='説明'),
        sa.Column('sync_type', sa.String(length=20), nullable=False, comment='同期タイプ（full/incremental）'),
        sa.Column('relative_preset', sa.String(length=30), nullable=True, comment='相対日付プリセット（last7days等）'),
        sa.Column('data_source_id', sa.Integer(), nullable=False, comment='データソースID'),
        sa.Column('schedule_type', sa.String(length=20), server_default='daily', nullable=True, comment='スケジュールタイプ（daily/weekly/monthly）'),
        sa.Column('execution_time', sa.Time(), nullable=False, comment='実行時刻（JST）'),
        sa.Column('day_of_week', sa.Integer(), nullable=True, comment='実行曜日（0=月曜日、週次の場合）'),
        sa.Column('day_of_month', sa.Integer(), nullable=True, comment='実行日（月次の場合）'),
        sa.Column('timezone', sa.String(length=50), server_default='Asia/Tokyo', nullable=True, comment='タイムゾーン'),
        sa.Column('is_enabled', sa.Boolean(), server_default='true', nullable=True, comment='有効フラグ'),
        sa.Column('last_execution_at', sa.DateTime(), nullable=True, comment='最終実行日時'),
        sa.Column('last_execution_status', sa.String(length=20), nullable=True, comment='最終実行ステータス'),
        sa.Column('last_execution_message', sa.Text(), nullable=True, comment='最終実行メッセージ'),
        sa.Column('last_sync_count', sa.Integer(), nullable=True, comment='最終同期件数'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_daily_quote_schedules_is_enabled', 'daily_quote_schedules', ['is_enabled'], unique=False)
    op.create_index('ix_daily_quote_schedules_schedule_type', 'daily_quote_schedules', ['schedule_type'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_daily_quote_schedules_schedule_type', table_name='daily_quote_schedules')
    op.drop_index('ix_daily_quote_schedules_is_enabled', table_name='daily_quote_schedules')
    op.drop_table('daily_quote_schedules')