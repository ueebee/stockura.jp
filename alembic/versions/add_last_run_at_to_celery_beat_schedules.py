"""Add last_run_at column to celery_beat_schedules table

Revision ID: b1c2d3e4f5g6
Revises: a3aa5ea18e77
Create Date: 2025-08-12 11:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b1c2d3e4f5g6'
down_revision = 'a3aa5ea18e77'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add last_run_at column to celery_beat_schedules table
    op.add_column('celery_beat_schedules', 
        sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True)
    )
    
    # Create index for performance
    op.create_index(
        'idx_celery_beat_schedules_last_run_at', 
        'celery_beat_schedules', 
        ['last_run_at']
    )


def downgrade() -> None:
    # Drop index
    op.drop_index('idx_celery_beat_schedules_last_run_at', table_name='celery_beat_schedules')
    
    # Drop column
    op.drop_column('celery_beat_schedules', 'last_run_at')