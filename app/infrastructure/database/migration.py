"""Alembic migration helper functions."""
import asyncio
from pathlib import Path
from typing import Optional

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


def get_alembic_config() -> Config:
    """Get Alembic configuration.
    
    Returns:
        Alembic Config object
    """
    root_path = Path(__file__).resolve().parent.parent.parent.parent
    alembic_ini_path = root_path / "alembic.ini"
    
    if not alembic_ini_path.exists():
        raise FileNotFoundError(f"alembic.ini not found at {alembic_ini_path}")
    
    alembic_cfg = Config(str(alembic_ini_path))
    alembic_cfg.set_main_option("script_location", str(root_path / "alembic"))
    
    return alembic_cfg


async def upgrade_database(revision: str = "head") -> None:
    """Upgrade database to specified revision.
    
    Args:
        revision: Target revision (default: "head")
    """
    def run_upgrade():
        alembic_cfg = get_alembic_config()
        logger.info(f"Upgrading database to revision: {revision}")
        command.upgrade(alembic_cfg, revision)
        logger.info("Database upgrade completed")
    
    await asyncio.get_event_loop().run_in_executor(None, run_upgrade)


async def downgrade_database(revision: str = "-1") -> None:
    """Downgrade database to specified revision.
    
    Args:
        revision: Target revision (default: "-1" for previous revision)
    """
    def run_downgrade():
        alembic_cfg = get_alembic_config()
        logger.info(f"Downgrading database to revision: {revision}")
        command.downgrade(alembic_cfg, revision)
        logger.info("Database downgrade completed")
    
    await asyncio.get_event_loop().run_in_executor(None, run_downgrade)


async def create_revision(message: str, autogenerate: bool = True) -> None:
    """Create new migration revision.
    
    Args:
        message: Revision message
        autogenerate: Whether to autogenerate migration from model changes
    """
    def run_revision():
        alembic_cfg = get_alembic_config()
        logger.info(f"Creating new revision: {message}")
        command.revision(alembic_cfg, message=message, autogenerate=autogenerate)
        logger.info("New revision created")
    
    await asyncio.get_event_loop().run_in_executor(None, run_revision)


def get_current_revision() -> Optional[str]:
    """Get current database revision.
    
    Returns:
        Current revision ID or None if no migrations applied
    """
    from alembic.runtime.migration import MigrationContext
    from sqlalchemy import create_engine
    
    # Create synchronous engine for this operation
    engine = create_engine(settings.database_url.replace("postgresql+asyncpg", "postgresql"))
    
    with engine.connect() as connection:
        context = MigrationContext.configure(connection)
        return context.get_current_revision()


def show_history() -> None:
    """Show migration history."""
    alembic_cfg = get_alembic_config()
    logger.info("Showing migration history")
    command.history(alembic_cfg)


async def check_pending_migrations() -> bool:
    """Check if there are pending migrations.
    
    Returns:
        True if there are pending migrations, False otherwise
    """
    def check_pending():
        alembic_cfg = get_alembic_config()
        script_dir = ScriptDirectory.from_config(alembic_cfg)
        
        # Get current revision
        current_rev = get_current_revision()
        
        # Get head revision
        head_rev = script_dir.get_current_head()
        
        if current_rev is None:
            # No migrations applied yet
            return bool(head_rev)
        
        return current_rev != head_rev
    
    return await asyncio.get_event_loop().run_in_executor(None, check_pending)


async def init_database() -> None:
    """Initialize database with all migrations.
    
    This is useful for setting up a new database from scratch.
    """
    logger.info("Initializing database with all migrations")
    await upgrade_database("head")


async def reset_database() -> None:
    """Reset database by downgrading to base and upgrading to head.
    
    WARNING: This will delete all data!
    """
    logger.warning("Resetting database - all data will be lost!")
    await downgrade_database("base")
    await upgrade_database("head")
    logger.info("Database reset completed")