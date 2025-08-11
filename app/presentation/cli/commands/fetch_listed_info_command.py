"""Fetch listed info CLI command."""
import asyncio
import sys
from datetime import date, datetime
from typing import Optional

import click

from app.application.use_cases.fetch_listed_info import FetchListedInfoUseCase
from app.core.config import settings
from app.presentation.cli.error_handler import handle_cli_errors
from app.core.logger import get_logger
from app.domain.entities.auth import JQuantsCredentials
from app.domain.value_objects.stock_code import StockCode
from app.domain.exceptions.listed_info_exceptions import (
    ListedInfoAPIError,
    ListedInfoDataError,
)
from app.presentation.dependencies.cli import (
    get_cli_session,
    get_cli_auth_repository,
    get_cli_listed_info_repository,
    get_cli_jquants_client,
)

logger = get_logger(__name__)


async def authenticate_jquants(email: str, password: str) -> JQuantsCredentials:
    """J-Quants API の認証を行う
    
    Args:
        email: J-Quants アカウントのメールアドレス
        password: J-Quants アカウントのパスワード
        
    Returns:
        JQuantsCredentials: 認証情報
        
    Raises:
        UnauthorizedError: 認証に失敗した場合
    """
    auth_repo = await get_cli_auth_repository()
    
    # リフレッシュトークンを取得
    refresh_token = await auth_repo.get_refresh_token(email, password)
    if not refresh_token:
        from app.presentation.exceptions import UnauthorizedError
        raise UnauthorizedError("J-Quants API の認証に失敗しました。")
    
    # ID トークンを取得
    id_token = await auth_repo.get_id_token(refresh_token)
    if not id_token:
        from app.presentation.exceptions import UnauthorizedError
        raise UnauthorizedError("ID トークンの取得に失敗しました。")
    
    # 認証情報を作成
    credentials = JQuantsCredentials(
        email=email,
        password=password,
        refresh_token=refresh_token,
        id_token=id_token
    )
    
    # 認証情報を保存（オプション）
    await auth_repo.save_credentials(credentials)
    
    return credentials


@click.command()
@click.option(
    "--code",
    "-c",
    default=None,
    help="銘柄コード（4 桁の数字）。指定しない場合は全銘柄を取得",
)
@click.option(
    "--date",
    "-d",
    default=None,
    help="基準日（YYYYMMDD 形式）。指定しない場合は最新データを取得",
)
@click.option(
    "--email",
    "-e",
    default=None,
    help="J-Quants API のメールアドレス",
)
@click.option(
    "--password",
    "-p",
    default=None,
    help="J-Quants API のパスワード",
)
@handle_cli_errors
def fetch_listed_info(
    code: Optional[str],
    date: Optional[str],
    email: Optional[str],
    password: Optional[str],
) -> None:
    """J-Quants API から上場銘柄情報を取得してデータベースに保存する"""
    asyncio.run(
        _fetch_listed_info_async(
            code=code,
            date=date,
            email=email,
            password=password,
        )
    )


async def _fetch_listed_info_async(
    code: Optional[str],
    date: Optional[str],
    email: Optional[str],
    password: Optional[str],
) -> None:
    """非同期で上場銘柄情報を取得"""
    # 日付のパース
    target_date = None
    if date:
        try:
            target_date = datetime.strptime(date, "%Y%m%d").date()
        except ValueError:
            from app.presentation.exceptions import ValidationError
            raise ValidationError(f"無効な日付形式です: {date}")

    # 認証情報の取得
    jquants_email = email or settings.jquants_email
    jquants_password = password or settings.jquants_password

    if not jquants_email or not jquants_password:
        from app.presentation.exceptions import ValidationError
        raise ValidationError(
            "J-Quants API の認証情報が設定されていません。\n"
            "--email と --password オプションを指定するか、"
            "環境変数 JQUANTS_EMAIL と JQUANTS_PASSWORD を設定してください。"
        )

    click.echo("J-Quants API に接続中...")

    # 認証処理
    credentials = await authenticate_jquants(jquants_email, jquants_password)
    click.echo("認証成功")

    # データベースセッションとリポジトリの初期化
    async for session in get_cli_session():
        # クライアントとリポジトリの初期化
        jquants_client = await get_cli_jquants_client(credentials)
        repository = await get_cli_listed_info_repository(session)

        # ユースケースの実行
        use_case = FetchListedInfoUseCase(
            jquants_client=jquants_client,
            listed_info_repository=repository,
            logger=logger,
        )

        click.echo(f"データ取得中... (code: {code or '全銘柄'}, date: {date or '最新'})")

        # 実行
        result = await use_case.execute(code=code, target_date=target_date)

        # 結果の表示
        if result.success:
            click.echo(
                f"\n✅ 処理完了:\n"
                f"  - 取得件数: {result.fetched_count}件\n"
                f"  - 保存件数: {result.saved_count}件"
            )
        else:
            from app.presentation.exceptions import PresentationError
            raise PresentationError(
                f"処理失敗: {result.error_message}",
                error_code="FETCH_FAILED",
                details={
                    "fetched_count": result.fetched_count,
                    "saved_count": result.saved_count
                }
            )

        # セッションのコミット
        await session.commit()


if __name__ == "__main__":
    fetch_listed_info()