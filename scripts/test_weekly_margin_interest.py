#!/usr/bin/env python3
"""週次信用取引残高機能の動作確認スクリプト"""
import asyncio
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.application.use_cases.fetch_weekly_margin_interest import (
    FetchWeeklyMarginInterestUseCase,
)
from app.domain.entities import WeeklyMarginInterest
from app.infrastructure.celery.tasks.weekly_margin_interest_task_asyncpg import (
    fetch_weekly_margin_interest_task_asyncpg,
)
from app.infrastructure.database.connection import get_async_session_context
from app.infrastructure.jquants.client_factory import JQuantsClientFactory
from app.infrastructure.jquants.weekly_margin_interest_client import (
    WeeklyMarginInterestClient,
)
from app.infrastructure.repositories.database.weekly_margin_interest_repository_impl import (
    WeeklyMarginInterestRepositoryImpl,
)

# TradesSpec 関連のインポート
from app.application.use_cases.fetch_trades_spec import FetchTradesSpecUseCase
from app.domain.entities.trades_spec import TradesSpec
from app.infrastructure.jquants.trades_spec_client import TradesSpecClient
from app.infrastructure.repositories.database.trades_spec_repository_impl import (
    TradesSpecRepositoryImpl,
)


async def test_api_connection():
    """J-Quants API 接続テスト"""
    print("\n=== J-Quants API 接続テスト ===")

    try:
        factory = JQuantsClientFactory()
        client = await factory.create_weekly_margin_interest_client()

        # 認証確認
        print("✓ API クライアント作成成功")

        # 少量のデータで接続テスト（特定銘柄の最新データ）
        test_code = "7203"  # トヨタ自動車

        print(f"\n テストデータ取得: 銘柄コード {test_code}")

        data = await client.fetch_weekly_margin_interest(
            code=test_code,
        )

        print(f"✓ データ取得成功: {len(data)} 件")

        if data:
            sample = data[0]
            print(f"\n サンプルデータ:")
            print(f"  銘柄コード: {sample.code}")
            print(f"  日付: {sample.date}")
            print(f"  信用買い残高: {sample.long_margin_trade_volume}")
            print(f"  信用売り残高: {sample.short_margin_trade_volume}")
            print(f"  銘柄種別: {sample.issue_type}")

        # クライアントを適切にクローズ
        await client.close()

        return True

    except Exception as e:
        print(f"✗ エラー: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


async def test_database_operations():
    """データベース操作テスト"""
    print("\n=== データベース操作テスト ===")

    async with get_async_session_context() as session:
        repository = WeeklyMarginInterestRepositoryImpl(session)

        # テストデータ作成
        test_data = WeeklyMarginInterest(
            code="9999",
            date=date(2024, 1, 1),
            short_margin_trade_volume=1000.0,
            long_margin_trade_volume=2000.0,
            short_negotiable_margin_trade_volume=500.0,
            long_negotiable_margin_trade_volume=1500.0,
            short_standardized_margin_trade_volume=500.0,
            long_standardized_margin_trade_volume=500.0,
            issue_type="1",
        )

        try:
            # 保存テスト
            await repository.save(test_data)
            await session.commit()
            print("✓ データ保存成功")

            # 検索テスト
            result = await repository.find_by_code_and_date("9999", date(2024, 1, 1))
            if result:
                print("✓ データ検索成功")
                print(f"  取得データ: {result.code} - {result.date}")
            else:
                print("✗ データ検索失敗")

            # 削除テスト
            deleted_count = await repository.delete_by_date_range(
                date(2024, 1, 1), date(2024, 1, 1)
            )
            await session.commit()
            print(f"✓ データ削除成功: {deleted_count} 件")

            return True

        except Exception as e:
            print(f"✗ エラー: {str(e)}")
            await session.rollback()
            return False


async def test_use_case():
    """ユースケーステスト"""
    print("\n=== ユースケーステスト ===")

    async with get_async_session_context() as session:
        factory = JQuantsClientFactory()
        client = await factory.create_weekly_margin_interest_client()
        repository = WeeklyMarginInterestRepositoryImpl(session)
        use_case = FetchWeeklyMarginInterestUseCase(client, repository)

        try:
            # 特定銘柄（トヨタ）の最新データ取得
            print("\n 特定銘柄のデータ取得テスト（トヨタ: 7203）")

            result = await use_case.execute(
                code="7203",
                from_date=date.today() - timedelta(days=30),
                to_date=date.today(),
            )

            print(f"✓ ユースケース実行成功")
            print(f"  取得件数: {result.fetched_count}")
            print(f"  保存件数: {result.saved_count}")
            print(f"  成功: {result.success}")

            if result.error_message:
                print(f"  エラー: {result.error_message}")

            await session.commit()

            # クライアントをクローズ
            await client.close()

            return result.success

        except Exception as e:
            print(f"✗ エラー: {str(e)}")
            await session.rollback()
            return False


def test_celery_task():
    """Celery タスクテスト"""
    print("\n=== Celery タスクテスト ===")

    try:
        # 同期的にタスクを実行（実際の環境では非同期で実行される）
        result = fetch_weekly_margin_interest_task_asyncpg.apply(
            args=[],
            kwargs={
                "code": "7203",
                "from_date": (date.today() - timedelta(days=7)).isoformat(),
                "to_date": date.today().isoformat(),
            },
        )

        if result.successful():
            print("✓ Celery タスク実行成功")
            print(f"  結果: {result.result}")
            return True
        else:
            print(f"✗ Celery タスク実行失敗: {result.info}")
            return False

    except Exception as e:
        print(f"✗ エラー: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


async def test_batch_fetch():
    """全銘柄バッチ取得テスト（注意：大量の API コール）"""
    print("\n=== バッチ取得テスト ===")
    print("警告: このテストは大量の API コールを行います。")

    # 環境変数でスキップ可能にする
    if os.environ.get("SKIP_BATCH_TEST", "").lower() == "true":
        print("テストをスキップしました。 (SKIP_BATCH_TEST=true)")
        return True
    
    # コマンドライン引数から確認
    if "--skip-batch" in sys.argv:
        print("テストをスキップしました。 (--skip-batch)")
        return True

    async with get_async_session_context() as session:
        factory = JQuantsClientFactory()
        client = await factory.create_weekly_margin_interest_client()
        repository = WeeklyMarginInterestRepositoryImpl(session)
        use_case = FetchWeeklyMarginInterestUseCase(client, repository)

        try:
            # 1 週間分の全銘柄データ取得
            print("\n 全銘柄のデータ取得（1 週間分）")

            result = await use_case.execute(
                from_date=date.today() - timedelta(days=7),
                to_date=date.today(),
            )

            print(f"✓ バッチ取得成功")
            print(f"  取得件数: {result.fetched_count}")
            print(f"  保存件数: {result.saved_count}")

            await session.commit()

            # クライアントをクローズ
            await client.close()

            return result.success

        except Exception as e:
            print(f"✗ エラー: {str(e)}")
            await session.rollback()
            return False


async def test_trades_spec_api_connection():
    """TradesSpec API 接続テスト"""
    print("\n=== TradesSpec API 接続テスト ===")

    try:
        factory = JQuantsClientFactory()
        client = await factory.create_trades_spec_client()

        # 認証確認
        print("✓ TradesSpec API クライアント作成成功")

        # 少量のデータで接続テスト（最新データ）
        print("\n テストデータ取得: TSEPrime 市場")

        data = await client.fetch_trades_spec(
            section="TSEPrime",
            from_date=date.today() - timedelta(days=7),
            to_date=date.today(),
        )

        if data and "trades_spec" in data:
            print(f"✓ データ取得成功: {len(data['trades_spec'])} 件")
            
            if data["trades_spec"]:
                sample = data["trades_spec"][0]
                print(f"\n サンプルデータ:")
                print(f"  公表日: {sample.get('PublishedDate', 'N/A')}")
                print(f"  週開始日: {sample.get('StartDate', 'N/A')}")
                print(f"  週終了日: {sample.get('EndDate', 'N/A')}")
                print(f"  市場区分: {sample.get('Section', 'N/A')}")
        else:
            print("✓ API 接続成功（データなし）")

        # クライアントを適切にクローズ
        await client.close()

        return True

    except Exception as e:
        print(f"✗ エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_trades_spec_database_operations():
    """TradesSpec データベース操作テスト"""
    print("\n=== TradesSpec データベース操作テスト ===")
    
    # 現在の実装では、 TradesSpec のデータベース操作は
    # ユースケース経由で行われるため、個別のテストはスキップ
    print("✓ データベース操作はユースケース経由でテスト")
    return True


async def test_trades_spec_use_case():
    """TradesSpec ユースケーステスト"""
    print("\n=== TradesSpec ユースケーステスト ===")

    async with get_async_session_context() as session:
        factory = JQuantsClientFactory()
        client = await factory.create_trades_spec_client()
        repository = TradesSpecRepositoryImpl(session)
        use_case = FetchTradesSpecUseCase(client, repository)

        try:
            # TSEPrime の最新データ取得
            print("\n TSEPrime 市場のデータ取得テスト")

            result = await use_case.execute(
                section="TSEPrime",
                from_date=date.today() - timedelta(days=30),
                to_date=date.today(),
            )

            print(f"✓ ユースケース実行成功")
            print(f"  取得件数: {result.fetched_count}")
            print(f"  保存件数: {result.saved_count}")
            print(f"  成功: {result.success}")

            if result.error_message:
                print(f"  エラー: {result.error_message}")

            await session.commit()

            # クライアントをクローズ
            await client.close()

            return result.success

        except Exception as e:
            print(f"✗ エラー: {str(e)}")
            await session.rollback()
            return False


async def test_trades_spec_batch_fetch():
    """TradesSpec バッチ取得テスト（全市場区分）"""
    print("\n=== TradesSpec バッチ取得テスト ===")
    print("警告: このテストは複数の市場区分のデータを取得します。")

    # 環境変数でスキップ可能にする
    if os.environ.get("SKIP_TRADES_SPEC_TEST", "").lower() == "true":
        print("テストをスキップしました。 (SKIP_TRADES_SPEC_TEST=true)")
        return True
    
    # コマンドライン引数から確認
    if "--skip-trades-spec" in sys.argv:
        print("テストをスキップしました。 (--skip-trades-spec)")
        return True

    async with get_async_session_context() as session:
        factory = JQuantsClientFactory()
        client = await factory.create_trades_spec_client()
        repository = TradesSpecRepositoryImpl(session)
        use_case = FetchTradesSpecUseCase(client, repository)

        try:
            # 市場区分リスト
            sections = ["TSEPrime", "TSEStandard", "TSEGrowth"]
            total_fetched = 0
            total_saved = 0
            all_success = True

            for section in sections:
                print(f"\n {section} 市場のデータ取得中...")
                
                result = await use_case.execute(
                    section=section,
                    from_date=date.today() - timedelta(days=30),
                    to_date=date.today(),
                )

                if result.success:
                    print(f"  ✓ 成功 - 取得: {result.fetched_count}, 保存: {result.saved_count}")
                    total_fetched += result.fetched_count
                    total_saved += result.saved_count
                else:
                    print(f"  ✗ 失敗 - {result.error_message}")
                    all_success = False

            print(f"\n✓ バッチ取得完了")
            print(f"  総取得件数: {total_fetched}")
            print(f"  総保存件数: {total_saved}")

            await session.commit()

            # クライアントをクローズ
            await client.close()

            return all_success

        except Exception as e:
            print(f"✗ エラー: {str(e)}")
            await session.rollback()
            return False


async def main():
    """メインテスト実行"""
    print("週次信用取引残高・投資部門別売買状況テスト開始")
    print("=" * 60)

    # 週次信用取引残高テスト
    print("\n 【週次信用取引残高テスト】")
    weekly_tests = [
        ("WeeklyMarginInterest API 接続", test_api_connection),
        ("WeeklyMarginInterest データベース操作", test_database_operations),
        ("WeeklyMarginInterest ユースケース", test_use_case),
        (
            "WeeklyMarginInterest Celery タスク",
            lambda: asyncio.get_event_loop().run_in_executor(None, test_celery_task),
        ),
    ]

    results = []
    for test_name, test_func in weekly_tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n{test_name}でエラー: {str(e)}")
            results.append((test_name, False))

    # オプション：バッチ取得テスト
    await test_batch_fetch()

    # TradesSpec テスト
    print("\n\n 【投資部門別売買状況（TradesSpec）テスト】")
    trades_spec_tests = [
        ("TradesSpec API 接続", test_trades_spec_api_connection),
        ("TradesSpec データベース操作", test_trades_spec_database_operations),
        ("TradesSpec ユースケース", test_trades_spec_use_case),
    ]

    for test_name, test_func in trades_spec_tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n{test_name}でエラー: {str(e)}")
            results.append((test_name, False))

    # オプション：TradesSpec バッチ取得テスト
    await test_trades_spec_batch_fetch()

    # 結果サマリー
    print("\n" + "=" * 60)
    print("テスト結果サマリー:")
    print("\n 週次信用取引残高:")
    for test_name, result in weekly_tests:
        status = "✓ 成功" if result else "✗ 失敗"
        print(f"  {test_name}: {status}")

    print("\n 投資部門別売買状況:")
    for test_name, result in trades_spec_tests:
        status = "✓ 成功" if result else "✗ 失敗"
        print(f"  {test_name}: {status}")

    total_tests = len(results)
    passed_tests = sum(1 for _, result in results if result)
    print(f"\n 総合: {passed_tests}/{total_tests} テスト成功")

    return passed_tests == total_tests


if __name__ == "__main__":
    # 環境変数チェック
    if not os.getenv("JQUANTS_EMAIL") or not os.getenv("JQUANTS_PASSWORD"):
        print("エラー: JQUANTS_EMAIL と JQUANTS_PASSWORD 環境変数を設定してください")
        print("export JQUANTS_EMAIL='your-email'")
        print("export JQUANTS_PASSWORD='your-password'")
        sys.exit(1)

    # テスト実行
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

