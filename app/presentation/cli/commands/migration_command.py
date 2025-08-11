"""Database migration CLI commands."""
import asyncio

import click

from app.core.logger import get_logger
from app.presentation.dependencies.migration import get_migration_service

logger = get_logger(__name__)


@click.group(name="db")
def db_group():
    """Database migration commands."""
    pass


@db_group.command()
@click.option("--revision", default="head", help="Target revision (default: head)")
def upgrade(revision: str):
    """Upgrade database to a revision."""
    try:
        service = get_migration_service()
        asyncio.run(service.upgrade_database(revision))
        click.echo(f"✅ Database upgraded to revision: {revision}")
    except Exception as e:
        click.echo(f"❌ Failed to upgrade database: {e}", err=True)
        raise click.Abort()


@db_group.command()
@click.option("--revision", default="-1", help="Target revision (default: -1)")
def downgrade(revision: str):
    """Downgrade database to a revision."""
    try:
        service = get_migration_service()
        asyncio.run(service.downgrade_database(revision))
        click.echo(f"✅ Database downgraded to revision: {revision}")
    except Exception as e:
        click.echo(f"❌ Failed to downgrade database: {e}", err=True)
        raise click.Abort()


@db_group.command()
@click.option("--message", "-m", required=True, help="Revision message")
@click.option("--autogenerate/--no-autogenerate", default=True, help="Autogenerate migration")
def revision(message: str, autogenerate: bool):
    """Create a new migration revision."""
    try:
        service = get_migration_service()
        asyncio.run(service.create_revision(message, autogenerate))
        click.echo(f"✅ Created new revision: {message}")
    except Exception as e:
        click.echo(f"❌ Failed to create revision: {e}", err=True)
        raise click.Abort()


@db_group.command()
def current():
    """Show current revision."""
    try:
        service = get_migration_service()
        current_rev = service.get_current_revision()
        if current_rev:
            click.echo(f"Current revision: {current_rev}")
        else:
            click.echo("No migrations applied yet")
    except Exception as e:
        click.echo(f"❌ Failed to get current revision: {e}", err=True)
        raise click.Abort()


@db_group.command()
def history():
    """Show migration history."""
    try:
        service = get_migration_service()
        service.show_history()
    except Exception as e:
        click.echo(f"❌ Failed to show history: {e}", err=True)
        raise click.Abort()


@db_group.command()
def check():
    """Check for pending migrations."""
    try:
        service = get_migration_service()
        has_pending = asyncio.run(service.check_pending_migrations())
        if has_pending:
            click.echo("⚠️  There are pending migrations. Run 'db upgrade' to apply them.")
        else:
            click.echo("✅ Database is up to date")
    except Exception as e:
        click.echo(f"❌ Failed to check migrations: {e}", err=True)
        raise click.Abort()


@db_group.command()
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
def init(yes: bool):
    """Initialize database with all migrations."""
    if not yes:
        click.confirm("This will initialize the database. Continue?", abort=True)
    try:
        service = get_migration_service()
        asyncio.run(service.init_database())
        click.echo("✅ Database initialized successfully")
    except Exception as e:
        click.echo(f"❌ Failed to initialize database: {e}", err=True)
        raise click.Abort()


@db_group.command()
def reset():
    """Reset database (WARNING: deletes all data)."""
    click.confirm(
        "⚠️  WARNING: This will DELETE ALL DATA in the database. Are you sure?",
        abort=True
    )
    click.confirm(
        "⚠️  This action cannot be undone. Type 'yes' to confirm",
        abort=True
    )
    try:
        service = get_migration_service()
        asyncio.run(service.reset_database())
        click.echo("✅ Database reset successfully")
    except Exception as e:
        click.echo(f"❌ Failed to reset database: {e}", err=True)
        raise click.Abort()


# Register commands to main CLI
def register_commands(cli):
    """Register migration commands to main CLI."""
    cli.add_command(db_group)