"""add_initial_data_sources

Revision ID: 01125040a15b
Revises: 2c86595eaba4
Create Date: 2025-06-22 11:18:35.171883

"""
from typing import Sequence, Union
import json
import os
from datetime import datetime
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '01125040a15b'
down_revision: Union[str, None] = '2c86595eaba4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # アプリケーション設定をインポート
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    
    from app.config import settings
    from app.services.encryption import get_encryption_service
    
    # 暗号化サービスを初期化
    encryption_service = get_encryption_service()
    
    # データソーステーブルを取得
    data_sources = sa.table('data_sources',
        sa.column('id', sa.Integer),
        sa.column('name', sa.String),
        sa.column('description', sa.String),
        sa.column('provider_type', sa.String),
        sa.column('is_enabled', sa.Boolean),
        sa.column('base_url', sa.String),
        sa.column('api_version', sa.String),
        sa.column('rate_limit_per_minute', sa.Integer),
        sa.column('rate_limit_per_hour', sa.Integer),
        sa.column('rate_limit_per_day', sa.Integer),
        sa.column('encrypted_credentials', sa.LargeBinary),
        sa.column('created_at', sa.DateTime),
        sa.column('updated_at', sa.DateTime),
    )
    
    # 現在時刻
    now = datetime.utcnow()
    
    # 初期データソースの定義
    initial_data_sources = [
        {
            'name': 'J-Quants API',
            'description': 'J-Quants API for Japanese stock data',
            'provider_type': 'jquants',
            'is_enabled': True,
            'base_url': 'https://api.jquants.com',
            'api_version': 'v1',
            'rate_limit_per_minute': 60,
            'rate_limit_per_hour': 3600,
            'rate_limit_per_day': 86400,
            'credentials': {
                'mailaddress': settings.JQUANTS_MAILADDRESS,
                'password': settings.JQUANTS_PASSWORD
            }
        },
        {
            'name': 'Yahoo Finance API',
            'description': 'Yahoo Finance API for global stock data (no authentication required)',
            'provider_type': 'yfinance',
            'is_enabled': True,
            'base_url': 'https://query1.finance.yahoo.com',
            'api_version': 'v8',
            'rate_limit_per_minute': 100,
            'rate_limit_per_hour': 5000,
            'rate_limit_per_day': 100000,
            'credentials': {}  # 認証不要のため空の辞書
        }
    ]
    
    # データソースを挿入
    for data_source in initial_data_sources:
        # 認証情報を暗号化（空の場合はNoneを保存）
        if data_source['credentials']:
            credentials_json = json.dumps(data_source['credentials'])
            encrypted_credentials = encryption_service.encrypt_data(credentials_json)
        else:
            encrypted_credentials = None
        
        # データを挿入
        op.execute(
            data_sources.insert().values(
                name=data_source['name'],
                description=data_source['description'],
                provider_type=data_source['provider_type'],
                is_enabled=data_source['is_enabled'],
                base_url=data_source['base_url'],
                api_version=data_source['api_version'],
                rate_limit_per_minute=data_source['rate_limit_per_minute'],
                rate_limit_per_hour=data_source['rate_limit_per_hour'],
                rate_limit_per_day=data_source['rate_limit_per_day'],
                encrypted_credentials=encrypted_credentials,
                created_at=now,
                updated_at=now
            )
        )


def downgrade() -> None:
    # 初期データソースを削除
    op.execute("DELETE FROM data_sources WHERE name IN ('J-Quants API', 'Yahoo Finance API')")
