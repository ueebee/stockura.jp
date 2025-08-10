#!/usr/bin/env python
"""listed_info スケジュール管理 CLI コマンド"""
import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import UUID

import click
from tabulate import tabulate

# プロジェクトルートを Python パスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.application.use_cases.manage_listed_info_schedule import (
    ManageListedInfoScheduleUseCase,
)
from app.domain.exceptions.schedule_exceptions import (
    ScheduleConflictException,
    ScheduleNotFoundException,
    ScheduleValidationException,
)
from app.domain.helpers.schedule_presets import list_presets, get_preset_description
from app.domain.validators.cron_validator import (
    get_cron_description,
    get_next_run_time,
    validate_cron_expression,
)
from app.infrastructure.database.database import get_async_session_context
from app.infrastructure.repositories.database.schedule_repository_impl import (
    ScheduleRepositoryImpl,
)


def get_use_case() -> ManageListedInfoScheduleUseCase:
    """ユースケースを取得"""
    # 簡易的な実装（本来は DI コンテナを使用）
    return ManageListedInfoScheduleUseCase(None)


async def async_get_use_case() -> ManageListedInfoScheduleUseCase:
    """非同期でユースケースを取得"""
    async with get_async_session_context() as session:
        repository = ScheduleRepositoryImpl(session)
        return ManageListedInfoScheduleUseCase(repository)


@click.group()
def cli():
    """listed_info スケジュール管理コマンド"""
    pass


@cli.command()
@click.option("--name", required=True, help="スケジュール名")
@click.option("--cron", help="cron 形式の実行スケジュール")
@click.option("--preset", help="プリセット名")
@click.option(
    "--period-type",
    required=True,
    type=click.Choice(["yesterday", "7days", "30days", "custom"]),
    help="データ取得期間",
)
@click.option("--description", help="スケジュールの説明")
@click.option("--codes", multiple=True, help="銘柄コード（複数指定可）")
@click.option("--market", help="市場コード")
@click.option("--enabled/--disabled", default=True, help="有効/無効（デフォルト: 有効）")
@click.option("--from-date", help="開始日 (YYYY-MM-DD) - period_type が custom の場合必須")
@click.option("--to-date", help="終了日 (YYYY-MM-DD) - period_type が custom の場合必須")
def create(
    name: str,
    cron: Optional[str],
    preset: Optional[str],
    period_type: str,
    description: Optional[str],
    codes: tuple,
    market: Optional[str],
    enabled: bool,
    from_date: Optional[str],
    to_date: Optional[str],
):
    """スケジュールを作成"""
    async def _create():
        try:
            # プリセットも cron も指定されていない場合はエラー
            if not cron and not preset:
                click.echo("エラー: --cron または--preset のいずれかを指定してください", err=True)
                return
            
            # period_type が custom の場合、 from_date と to_date が必須
            if period_type == "custom" and (not from_date or not to_date):
                click.echo("エラー: period_type が 'custom' の場合、--from-date と --to-date は必須です", err=True)
                return

            use_case = await async_get_use_case()
            schedule = await use_case.create_schedule(
                name=name,
                cron_expression=cron,
                period_type=period_type,
                description=description,
                enabled=enabled,
                codes=list(codes) if codes else None,
                market=market,
                preset_name=preset,
                from_date=from_date,
                to_date=to_date,
            )

            click.echo(f"スケジュールを作成しました: {schedule.name} (ID: {schedule.id})")
            
            # cron 式の説明を表示
            try:
                cron_desc = get_cron_description(schedule.cron_expression)
                next_run = get_next_run_time(schedule.cron_expression)
                click.echo(f"実行タイミング: {cron_desc}")
                click.echo(f"次回実行予定: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            except:
                pass

        except ScheduleConflictException as e:
            click.echo(f"エラー: {e}", err=True)
        except ScheduleValidationException as e:
            click.echo(f"バリデーションエラー: {e}", err=True)
        except Exception as e:
            click.echo(f"予期しないエラー: {e}", err=True)

    asyncio.run(_create())


@cli.command()
@click.option("--enabled-only", is_flag=True, help="有効なスケジュールのみ表示")
@click.option("--limit", default=100, help="表示件数（デフォルト: 100）")
def list(enabled_only: bool, limit: int):
    """スケジュール一覧を表示"""
    async def _list():
        try:
            use_case = await async_get_use_case()
            schedules = await use_case.list_schedules(
                category="listed_info",
                enabled_only=enabled_only,
                limit=limit,
            )

            if not schedules:
                click.echo("スケジュールが登録されていません")
                return

            # テーブル形式で表示
            headers = ["ID", "名前", "cron 式", "期間", "有効", "次回実行", "説明"]
            rows = []
            for s in schedules:
                period_type = s.kwargs.get("period_type", "-")
                next_run = s.next_run_at.strftime("%m/%d %H:%M") if s.next_run_at else "-"
                desc = (s.description[:30] + "...") if s.description and len(s.description) > 30 else s.description or "-"
                
                rows.append([
                    str(s.id)[:8],  # UUID の最初の 8 文字
                    s.name,
                    s.cron_expression,
                    period_type,
                    "○" if s.enabled else "×",
                    next_run,
                    desc,
                ])

            click.echo(tabulate(rows, headers=headers, tablefmt="grid"))
            click.echo(f"\n 合計: {len(schedules)}件")

        except Exception as e:
            click.echo(f"エラー: {e}", err=True)

    asyncio.run(_list())


@cli.command()
@click.argument("schedule_id", type=str)
def show(schedule_id: str):
    """スケジュールの詳細を表示"""
    async def _show():
        try:
            use_case = await async_get_use_case()
            schedule = await use_case.get_schedule(UUID(schedule_id))

            click.echo(f"スケジュール ID: {schedule.id}")
            click.echo(f"名前: {schedule.name}")
            click.echo(f"タスク名: {schedule.task_name}")
            click.echo(f"cron 式: {schedule.cron_expression}")
            
            # cron 式の説明
            try:
                cron_desc = get_cron_description(schedule.cron_expression)
                click.echo(f"実行タイミング: {cron_desc}")
            except:
                pass
            
            click.echo(f"有効: {'はい' if schedule.enabled else 'いいえ'}")
            click.echo(f"説明: {schedule.description or '(なし)'}")
            click.echo(f"カテゴリ: {schedule.category}")
            click.echo(f"タグ: {', '.join(schedule.tags) if schedule.tags else '(なし)'}")
            
            # kwargs の内容
            click.echo("\n パラメータ:")
            for key, value in schedule.kwargs.items():
                click.echo(f"  {key}: {value}")
            
            click.echo(f"\n 作成日時: {schedule.created_at}")
            click.echo(f"更新日時: {schedule.updated_at}")
            
            # 次回実行予定
            if hasattr(schedule, "next_run_at") and schedule.next_run_at:
                click.echo(f"次回実行予定: {schedule.next_run_at}")

        except ScheduleNotFoundException as e:
            click.echo(f"エラー: {e}", err=True)
        except ValueError:
            click.echo("エラー: 無効なスケジュール ID です", err=True)
        except Exception as e:
            click.echo(f"エラー: {e}", err=True)

    asyncio.run(_show())


@cli.command()
@click.argument("schedule_id", type=str)
@click.option("--name", help="新しいスケジュール名")
@click.option("--cron", help="新しい cron 式")
@click.option("--period-type", type=click.Choice(["yesterday", "7days", "30days", "custom"]))
@click.option("--description", help="新しい説明")
@click.option("--enabled/--disabled", default=None, help="有効/無効")
def update(
    schedule_id: str,
    name: Optional[str],
    cron: Optional[str],
    period_type: Optional[str],
    description: Optional[str],
    enabled: Optional[bool],
):
    """スケジュールを更新"""
    async def _update():
        try:
            use_case = await async_get_use_case()
            schedule = await use_case.update_schedule(
                schedule_id=UUID(schedule_id),
                name=name,
                cron_expression=cron,
                period_type=period_type,
                description=description,
                enabled=enabled,
            )

            click.echo(f"スケジュールを更新しました: {schedule.name}")

        except ScheduleNotFoundException as e:
            click.echo(f"エラー: {e}", err=True)
        except ScheduleConflictException as e:
            click.echo(f"エラー: {e}", err=True)
        except ScheduleValidationException as e:
            click.echo(f"バリデーションエラー: {e}", err=True)
        except ValueError:
            click.echo("エラー: 無効なスケジュール ID です", err=True)
        except Exception as e:
            click.echo(f"エラー: {e}", err=True)

    asyncio.run(_update())


@cli.command()
@click.argument("schedule_id", type=str)
@click.confirmation_option(prompt="本当に削除しますか？")
def delete(schedule_id: str):
    """スケジュールを削除"""
    async def _delete():
        try:
            use_case = await async_get_use_case()
            await use_case.delete_schedule(UUID(schedule_id))
            click.echo("スケジュールを削除しました")

        except ScheduleNotFoundException as e:
            click.echo(f"エラー: {e}", err=True)
        except ValueError:
            click.echo("エラー: 無効なスケジュール ID です", err=True)
        except Exception as e:
            click.echo(f"エラー: {e}", err=True)

    asyncio.run(_delete())


@cli.command()
@click.argument("schedule_id", type=str)
def toggle(schedule_id: str):
    """スケジュールの有効/無効を切り替え"""
    async def _toggle():
        try:
            use_case = await async_get_use_case()
            schedule = await use_case.toggle_schedule(UUID(schedule_id))
            
            status = "有効" if schedule.enabled else "無効"
            click.echo(f"スケジュールを{status}にしました: {schedule.name}")

        except ScheduleNotFoundException as e:
            click.echo(f"エラー: {e}", err=True)
        except ValueError:
            click.echo("エラー: 無効なスケジュール ID です", err=True)
        except Exception as e:
            click.echo(f"エラー: {e}", err=True)

    asyncio.run(_toggle())


@cli.command("validate-cron")
@click.argument("cron_expression")
def validate_cron(cron_expression: str):
    """cron 式を検証"""
    try:
        validate_cron_expression(cron_expression)
        click.echo(f"✓ 有効な cron 式です: {cron_expression}")
        
        # 説明を表示
        desc = get_cron_description(cron_expression)
        click.echo(f"実行タイミング: {desc}")
        
        # 次の 5 回の実行予定を表示
        click.echo("\n 次の 5 回の実行予定:")
        base_time = datetime.now()
        for i in range(5):
            next_time = get_next_run_time(cron_expression, base_time)
            click.echo(f"  {i+1}. {next_time.strftime('%Y-%m-%d %H:%M:%S (%a)')}")
            base_time = next_time

    except Exception as e:
        click.echo(f"✗ {e}", err=True)


@cli.command("list-presets")
@click.option("--category", help="カテゴリでフィルタ（daily, weekly, monthly, market, frequent）")
def list_presets_cmd(category: Optional[str]):
    """利用可能なプリセット一覧を表示"""
    presets = list_presets()
    
    if category:
        # カテゴリフィルタ
        from app.domain.helpers.schedule_presets import get_presets_by_category
        presets = get_presets_by_category(category)
    
    if not presets:
        click.echo("該当するプリセットがありません")
        return
    
    # テーブル形式で表示
    headers = ["プリセット名", "cron 式", "説明"]
    rows = []
    for name, info in sorted(presets.items()):
        rows.append([name, info["cron_expression"], info["description"]])
    
    click.echo(tabulate(rows, headers=headers, tablefmt="grid"))


if __name__ == "__main__":
    cli()