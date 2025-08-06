"""Fetch listed info CLI command."""
import asyncio
import sys
from datetime import date, datetime
from typing import Optional

import click

from app.application.use_cases.fetch_listed_info import FetchListedInfoUseCase
from app.core.config import settings
from app.core.logger import get_logger
from app.domain.entities.auth import JQuantsCredentials
from app.domain.value_objects.stock_code import StockCode
from app.domain.exceptions.listed_info_exceptions import (
    ListedInfoAPIError,
    ListedInfoDataError,
)
from app.infrastructure.database.connection import get_async_session_context
from app.infrastructure.repositories.database.listed_info_repository_impl import (
    ListedInfoRepositoryImpl,
)
from app.infrastructure.repositories.external.jquants_auth_repository_impl import JQuantsAuthRepository
from app.infrastructure.jquants.base_client import JQuantsBaseClient
from app.infrastructure.jquants.listed_info_client import JQuantsListedInfoClient

logger = get_logger(__name__)


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
    try:
        # 日付のパース
        target_date = None
        if date:
            try:
                target_date = datetime.strptime(date, "%Y%m%d").date()
            except ValueError:
                click.echo(f"エラー: 無効な日付形式です: {date}", err=True)
                sys.exit(1)

        # 認証情報の取得
        jquants_email = email or settings.jquants_email
        jquants_password = password or settings.jquants_password

        if not jquants_email or not jquants_password:
            click.echo(
                "エラー: J-Quants API の認証情報が設定されていません。\n"
                "--email と --password オプションを指定するか、"
                "環境変数 JQUANTS_EMAIL と JQUANTS_PASSWORD を設定してください。",
                err=True,
            )
            sys.exit(1)

        click.echo("J-Quants API に接続中...")

        # 認証
        auth_repo = JQuantsAuthRepository()
        
        # リフレッシュトークンを取得
        refresh_token = await auth_repo.get_refresh_token(jquants_email, jquants_password)
        if not refresh_token:
            click.echo("エラー: J-Quants API の認証に失敗しました。", err=True)
            sys.exit(1)
        
        # ID トークンを取得
        id_token = await auth_repo.get_id_token(refresh_token)
        if not id_token:
            click.echo("エラー: ID トークンの取得に失敗しました。", err=True)
            sys.exit(1)
        
        # 認証情報を作成
        credentials = JQuantsCredentials(
            email=jquants_email,
            password=jquants_password,
            refresh_token=refresh_token,
            id_token=id_token
        )
        
        # 認証情報を保存（オプション）
        await auth_repo.save_credentials(credentials)

        click.echo("認証成功")

        # データベースセッションとリポジトリの初期化
        async with get_async_session_context() as session:
            # クライアントとリポジトリの初期化
            base_client = JQuantsBaseClient(credentials)
            jquants_client = JQuantsListedInfoClient(base_client)
            repository = ListedInfoRepositoryImpl(session)

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
                click.echo(
                    f"\n❌ 処理失敗:\n"
                    f"  - エラー: {result.error_message}\n"
                    f"  - 取得件数: {result.fetched_count}件\n"
                    f"  - 保存件数: {result.saved_count}件",
                    err=True,
                )
                sys.exit(1)

            # セッションのコミット
            await session.commit()

    except KeyboardInterrupt:
        click.echo("\n 処理を中断しました。", err=True)
        sys.exit(130)
    except Exception as e:
        click.echo(f"\n 予期しないエラーが発生しました: {str(e)}", err=True)
        logger.exception("Unexpected error in fetch_listed_info command")
        sys.exit(1)


if __name__ == "__main__":
    fetch_listed_info()