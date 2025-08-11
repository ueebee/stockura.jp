"""Migration service dependency injection."""
from typing import Optional, Protocol


class MigrationService(Protocol):
    """Migration service interface."""

    async def upgrade_database(self, revision: str) -> None:
        """Upgrade database to a revision."""
        ...

    async def downgrade_database(self, revision: str) -> None:
        """Downgrade database to a revision."""
        ...

    async def create_revision(self, message: str, autogenerate: bool) -> None:
        """Create a new migration revision."""
        ...

    def get_current_revision(self) -> Optional[str]:
        """Get current database revision."""
        ...

    def show_history(self) -> None:
        """Show migration history."""
        ...

    async def check_pending_migrations(self) -> bool:
        """Check if there are pending migrations."""
        ...

    async def init_database(self) -> None:
        """Initialize database with all migrations."""
        ...

    async def reset_database(self) -> None:
        """Reset database (WARNING: deletes all data)."""
        ...


def get_migration_service() -> MigrationService:
    """Get migration service.
    
    Returns:
        MigrationService: Migration service implementation
    """
    # インフラストラクチャ層のマイグレーション関数をラップ
    from app.infrastructure.database import migration
    
    class MigrationServiceImpl:
        """Migration service implementation wrapping infrastructure functions."""
        
        async def upgrade_database(self, revision: str) -> None:
            await migration.upgrade_database(revision)
        
        async def downgrade_database(self, revision: str) -> None:
            await migration.downgrade_database(revision)
        
        async def create_revision(self, message: str, autogenerate: bool) -> None:
            await migration.create_revision(message, autogenerate)
        
        def get_current_revision(self) -> Optional[str]:
            return migration.get_current_revision()
        
        def show_history(self) -> None:
            migration.show_history()
        
        async def check_pending_migrations(self) -> bool:
            return await migration.check_pending_migrations()
        
        async def init_database(self) -> None:
            await migration.init_database()
        
        async def reset_database(self) -> None:
            await migration.reset_database()
    
    return MigrationServiceImpl()