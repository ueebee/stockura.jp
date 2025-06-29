"""add_daily_quotes_tables

Revision ID: 7606200b40c4
Revises: cbfb1c612bbe
Create Date: 2025-06-27 23:19:14.419580

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7606200b40c4'
down_revision: Union[str, None] = 'cbfb1c612bbe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # daily_quotes テーブルを作成
    op.create_table(
        'daily_quotes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=False, comment='銘柄コード'),
        sa.Column('trade_date', sa.Date(), nullable=False, comment='取引日'),
        
        # 調整前価格データ
        sa.Column('open_price', sa.DECIMAL(precision=10, scale=2), comment='始値'),
        sa.Column('high_price', sa.DECIMAL(precision=10, scale=2), comment='高値'),
        sa.Column('low_price', sa.DECIMAL(precision=10, scale=2), comment='安値'),
        sa.Column('close_price', sa.DECIMAL(precision=10, scale=2), comment='終値'),
        sa.Column('volume', sa.BigInteger(), comment='取引高'),
        sa.Column('turnover_value', sa.BigInteger(), comment='取引代金'),
        
        # 調整後価格データ
        sa.Column('adjustment_factor', sa.DECIMAL(precision=10, scale=6), comment='調整係数'),
        sa.Column('adjustment_open', sa.DECIMAL(precision=10, scale=2), comment='調整後始値'),
        sa.Column('adjustment_high', sa.DECIMAL(precision=10, scale=2), comment='調整後高値'),
        sa.Column('adjustment_low', sa.DECIMAL(precision=10, scale=2), comment='調整後安値'),
        sa.Column('adjustment_close', sa.DECIMAL(precision=10, scale=2), comment='調整後終値'),
        sa.Column('adjustment_volume', sa.BigInteger(), comment='調整後取引高'),
        
        # 制限フラグ
        sa.Column('upper_limit_flag', sa.Boolean(), default=False, comment='ストップ高フラグ'),
        sa.Column('lower_limit_flag', sa.Boolean(), default=False, comment='ストップ安フラグ'),
        
        # Premium限定（将来拡張用）
        sa.Column('morning_open', sa.DECIMAL(precision=10, scale=2), comment='前場始値'),
        sa.Column('morning_high', sa.DECIMAL(precision=10, scale=2), comment='前場高値'),
        sa.Column('morning_low', sa.DECIMAL(precision=10, scale=2), comment='前場安値'),
        sa.Column('morning_close', sa.DECIMAL(precision=10, scale=2), comment='前場終値'),
        sa.Column('morning_volume', sa.BigInteger(), comment='前場取引高'),
        sa.Column('morning_turnover_value', sa.BigInteger(), comment='前場取引代金'),
        
        sa.Column('afternoon_open', sa.DECIMAL(precision=10, scale=2), comment='後場始値'),
        sa.Column('afternoon_high', sa.DECIMAL(precision=10, scale=2), comment='後場高値'),
        sa.Column('afternoon_low', sa.DECIMAL(precision=10, scale=2), comment='後場安値'),
        sa.Column('afternoon_close', sa.DECIMAL(precision=10, scale=2), comment='後場終値'),
        sa.Column('afternoon_volume', sa.BigInteger(), comment='後場取引高'),
        sa.Column('afternoon_turnover_value', sa.BigInteger(), comment='後場取引代金'),
        
        # タイムスタンプ
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['code'], ['companies.code'], name='fk_daily_quotes_company_code'),
    )
    
    # daily_quotes_sync_history テーブルを作成
    op.create_table(
        'daily_quotes_sync_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sync_date', sa.Date(), nullable=False, comment='同期対象日'),
        sa.Column('sync_type', sa.String(length=20), nullable=False, comment='同期タイプ（full/incremental/single_stock）'),
        sa.Column('status', sa.String(length=20), nullable=False, comment='同期状態（running/completed/failed）'),
        
        # 統計情報
        sa.Column('target_companies', sa.Integer(), comment='対象企業数'),
        sa.Column('total_records', sa.Integer(), comment='総レコード数'),
        sa.Column('new_records', sa.Integer(), comment='新規レコード数'),
        sa.Column('updated_records', sa.Integer(), comment='更新レコード数'),
        sa.Column('skipped_records', sa.Integer(), comment='スキップレコード数'),
        
        # 実行情報
        sa.Column('started_at', sa.DateTime(), nullable=False, comment='開始時刻'),
        sa.Column('completed_at', sa.DateTime(), comment='完了時刻'),
        sa.Column('error_message', sa.Text(), comment='エラーメッセージ'),
        
        # 処理詳細
        sa.Column('from_date', sa.Date(), comment='処理開始日'),
        sa.Column('to_date', sa.Date(), comment='処理終了日'),
        sa.Column('specific_codes', sa.Text(), comment='特定銘柄指定（JSON配列）'),
        
        sa.PrimaryKeyConstraint('id'),
    )
    
    # インデックスを作成
    op.create_index('ix_daily_quotes_code_date', 'daily_quotes', ['code', 'trade_date'], unique=True)
    op.create_index('ix_daily_quotes_date', 'daily_quotes', ['trade_date'])
    op.create_index('ix_daily_quotes_code', 'daily_quotes', ['code'])
    op.create_index('ix_daily_quotes_volume', 'daily_quotes', ['volume'])
    op.create_index('ix_daily_quotes_code_date_desc', 'daily_quotes', ['code', 'trade_date'])
    op.create_index('ix_daily_quotes_id', 'daily_quotes', ['id'])
    
    op.create_index('ix_daily_quotes_sync_date_status', 'daily_quotes_sync_history', ['sync_date', 'status'])
    op.create_index('ix_daily_quotes_sync_started_at', 'daily_quotes_sync_history', ['started_at'])


def downgrade() -> None:
    # インデックスを削除
    op.drop_index('ix_daily_quotes_sync_started_at', table_name='daily_quotes_sync_history')
    op.drop_index('ix_daily_quotes_sync_date_status', table_name='daily_quotes_sync_history')
    
    op.drop_index('ix_daily_quotes_id', table_name='daily_quotes')
    op.drop_index('ix_daily_quotes_code_date_desc', table_name='daily_quotes')
    op.drop_index('ix_daily_quotes_volume', table_name='daily_quotes')
    op.drop_index('ix_daily_quotes_code', table_name='daily_quotes')
    op.drop_index('ix_daily_quotes_date', table_name='daily_quotes')
    op.drop_index('ix_daily_quotes_code_date', table_name='daily_quotes')
    
    # テーブルを削除
    op.drop_table('daily_quotes_sync_history')
    op.drop_table('daily_quotes')
