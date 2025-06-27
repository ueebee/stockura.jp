"""add_sector33_9999_code

Revision ID: 196afdc25a27
Revises: 1479a1bf7b47
Create Date: 2025-06-27 00:35:00.164355

"""
from typing import Sequence, Union
from datetime import datetime
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = '196afdc25a27'
down_revision: Union[str, None] = '1479a1bf7b47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """9999業種コードを追加"""
    connection = op.get_bind()
    current_time = datetime.utcnow()
    
    # 9999コードが存在するかチェック
    result = connection.execute(text("SELECT COUNT(*) FROM sector33_masters WHERE code = '9999'"))
    count = result.scalar()
    
    if count == 0:
        # 9999業種コードを追加
        connection.execute(text("""
            INSERT INTO sector33_masters (code, name, name_english, description, sector17_code, display_order, is_active, created_at, updated_at) 
            VALUES ('9999', 'その他', 'Others', 'その他の業種', '99', 34, true, :created_at, :updated_at)
        """), {"created_at": current_time, "updated_at": current_time})


def downgrade() -> None:
    """9999業種コードを削除"""
    connection = op.get_bind()
    connection.execute(text("DELETE FROM sector33_masters WHERE code = '9999'"))
