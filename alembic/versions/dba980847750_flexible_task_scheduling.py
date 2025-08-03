"""flexible_task_scheduling

Revision ID: dba980847750
Revises: 87e8a6480680
Create Date: 2025-07-31 12:51:12.170883

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "dba980847750"
down_revision: Union[str, None] = "87e8a6480680"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if constraint exists before dropping
    conn = op.get_bind()
    result = conn.execute(
        sa.text("""
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'celery_beat_schedules' 
            AND constraint_name = 'celery_beat_schedules_name_key'
            AND constraint_type = 'UNIQUE'
        """)
    ).fetchone()
    
    if result:
        # Drop UNIQUE constraint on name field
        op.drop_constraint('celery_beat_schedules_name_key', 'celery_beat_schedules', type_='unique')
    
    # Drop the unique index created in previous migration
    try:
        op.drop_index('ix_celery_beat_schedules_name', table_name='celery_beat_schedules')
    except Exception:
        # Index might not exist
        pass
    
    # Add non-unique index on name field for performance
    op.create_index('idx_celery_beat_schedules_name', 'celery_beat_schedules', ['name'])
    
    # Add new columns
    op.add_column('celery_beat_schedules', sa.Column('category', sa.String(length=50), nullable=True))
    op.add_column('celery_beat_schedules', sa.Column('tags', sa.dialects.postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False))
    op.add_column('celery_beat_schedules', sa.Column('execution_policy', sa.String(length=20), server_default='allow', nullable=False))
    op.add_column('celery_beat_schedules', sa.Column('auto_generated_name', sa.Boolean(), server_default='false', nullable=False))
    
    # Add check constraint for execution_policy
    op.create_check_constraint(
        'ck_celery_beat_schedules_execution_policy',
        'celery_beat_schedules',
        sa.column('execution_policy').in_(['allow', 'skip', 'queue'])
    )
    
    # Create indexes for new columns
    op.create_index('idx_celery_beat_schedules_category', 'celery_beat_schedules', ['category'])
    op.create_index('idx_celery_beat_schedules_tags', 'celery_beat_schedules', ['tags'], postgresql_using='gin')


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index('idx_celery_beat_schedules_tags', table_name='celery_beat_schedules')
    op.drop_index('idx_celery_beat_schedules_category', table_name='celery_beat_schedules')
    
    # Drop check constraint
    op.drop_constraint('ck_celery_beat_schedules_execution_policy', 'celery_beat_schedules', type_='check')
    
    # Drop columns
    op.drop_column('celery_beat_schedules', 'auto_generated_name')
    op.drop_column('celery_beat_schedules', 'execution_policy')
    op.drop_column('celery_beat_schedules', 'tags')
    op.drop_column('celery_beat_schedules', 'category')
    
    # Drop index on name field
    op.drop_index('idx_celery_beat_schedules_name', table_name='celery_beat_schedules')
    
    # Restore UNIQUE constraint on name field
    op.create_unique_constraint('celery_beat_schedules_name_key', 'celery_beat_schedules', ['name'])
