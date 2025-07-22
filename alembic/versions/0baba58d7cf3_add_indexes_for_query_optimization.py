"""add_indexes_for_query_optimization

Revision ID: 0baba58d7cf3
Revises: f68f6c59fbd6
Create Date: 2025-07-23 00:35:34.935982

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0baba58d7cf3'
down_revision: Union[str, None] = 'f68f6c59fbd6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # daily_quotes_sync_history用のインデックス
    op.create_index(
        'idx_daily_quotes_sync_history_started_at',
        'daily_quotes_sync_history',
        ['started_at'],
        postgresql_using='btree'
    )
    
    op.create_index(
        'idx_daily_quotes_sync_history_status',
        'daily_quotes_sync_history',
        ['status'],
        postgresql_using='btree'
    )
    
    # api_endpoint_schedules用のインデックス
    op.create_index(
        'idx_api_endpoint_schedules_endpoint_id',
        'api_endpoint_schedules',
        ['endpoint_id'],
        postgresql_using='btree'
    )
    
    # daily_quotes用の複合インデックス (既に存在するix_daily_quotes_code_dateがあるのでスキップ)
    # op.create_index(
    #     'idx_daily_quotes_code_date',
    #     'daily_quotes',
    #     ['code', 'trade_date'],
    #     postgresql_using='btree'
    # )
    
    # daily_quote_schedules用のインデックス
    op.create_index(
        'idx_daily_quote_schedules_data_source_enabled',
        'daily_quote_schedules',
        ['data_source_id', 'is_enabled'],
        postgresql_using='btree'
    )
    
    # api_endpoints用のインデックス
    op.create_index(
        'idx_api_endpoints_data_source_type',
        'api_endpoints',
        ['data_source_id', 'data_type'],
        postgresql_using='btree'
    )


def downgrade() -> None:
    # インデックスを削除
    op.drop_index('idx_api_endpoints_data_source_type', 'api_endpoints')
    op.drop_index('idx_daily_quote_schedules_data_source_enabled', 'daily_quote_schedules')
    # op.drop_index('idx_daily_quotes_code_date', 'daily_quotes')
    op.drop_index('idx_api_endpoint_schedules_endpoint_id', 'api_endpoint_schedules')
    op.drop_index('idx_daily_quotes_sync_history_status', 'daily_quotes_sync_history')
    op.drop_index('idx_daily_quotes_sync_history_started_at', 'daily_quotes_sync_history')
