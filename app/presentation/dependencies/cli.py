"""CLI commands dependency injection providers."""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.auth import JQuantsCredentials
from app.domain.repositories.auth_repository_interface import AuthRepositoryInterface
from app.domain.repositories.jquants_listed_info_repository_interface import JQuantsListedInfoRepositoryInterface


async def get_cli_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for CLI commands."""
    from app.infrastructure.database.connection import get_async_session_context

    async with get_async_session_context() as session:
        yield session


async def get_cli_auth_repository() -> AuthRepositoryInterface:
    """Get auth repository for CLI commands."""
    from app.infrastructure.repositories.external.jquants_auth_repository_impl import (
        JQuantsAuthRepository,
    )

    return JQuantsAuthRepository()


async def get_cli_listed_info_repository(
    session: AsyncSession,
) -> JQuantsListedInfoRepositoryInterface:
    """Get listed info repository for CLI commands."""
    from app.infrastructure.repositories.database.jquants_listed_info_repository_impl import (
        JQuantsListedInfoRepositoryImpl,
    )

    return JQuantsListedInfoRepositoryImpl(session)


async def get_cli_jquants_client(credentials: JQuantsCredentials):
    """Get J-Quants client for CLI commands."""
    from app.infrastructure.external_services.jquants.base_client import JQuantsBaseClient
    from app.infrastructure.external_services.jquants.listed_info_client import (
        JQuantsListedInfoClient,
    )

    base_client = JQuantsBaseClient(credentials)
    return JQuantsListedInfoClient(base_client)