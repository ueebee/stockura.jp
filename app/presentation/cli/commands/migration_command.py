"""Database migration CLI commands."""
import asyncio

import click

from app.core.logger import get_logger
from app.infrastructure.database.migration import (
    check_pending_migrations,
    create_revision,
    downgrade_database,
    get_current_revision,
    init_database,
    reset_database,
    show_history,
    upgrade_database,
)

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
        asyncio.run(upgrade_database(revision))
        click.echo(f"✅ Database upgraded to revision: {revision}")
    except Exception as e:
        click.echo(f"❌ Failed to upgrade database: {e}", err=True)
        raise click.Abort()


@db_group.command()
@click.option("--revision", default="-1", help="Target revision (default: -1)")
def downgrade(revision: str):
    """Downgrade database to a revision."""
    try:
        asyncio.run(downgrade_database(revision))
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
        asyncio.run(create_revision(message, autogenerate))
        click.echo(f"✅ Created new revision: {message}")
    except Exception as e:
        click.echo(f"❌ Failed to create revision: {e}", err=True)
        raise click.Abort()


@db_group.command()
def current():
    """Show current revision."""
    try:
        current_rev = get_current_revision()
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
        show_history()
    except Exception as e:
        click.echo(f"❌ Failed to show history: {e}", err=True)
        raise click.Abort()


@db_group.command()
def check():
    """Check for pending migrations."""
    try:
        has_pending = asyncio.run(check_pending_migrations())
        if has_pending:
            click.echo("⚠️  There are pending migrations. Run 'db upgrade' to apply them.")
        else:
            click.echo("✅ Database is up to date")
    except Exception as e:
        click.echo(f"❌ Failed to check migrations: {e}", err=True)
        raise click.Abort()


@db_group.command()
def init():
    """Initialize database with all migrations."""
    click.confirm("This will initialize the database. Continue?", abort=True)
    try:
        asyncio.run(init_database())
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
        asyncio.run(reset_database())
        click.echo("✅ Database reset successfully")
    except Exception as e:
        click.echo(f"❌ Failed to reset database: {e}", err=True)
        raise click.Abort()


# Register commands to main CLI
def register_commands(cli):
    """Register migration commands to main CLI."""
    cli.add_command(db_group)