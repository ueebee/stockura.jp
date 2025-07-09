#!/usr/bin/env python3
"""
J-Quants API株価データ取得テストスクリプト
"""

import asyncio
import sys
import os
from datetime import datetime, date, timedelta
from typing import List

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.session import async_session_maker
from app.services.data_source_service import DataSourceService
from app.services.jquants_client import JQuantsClientManager
from app.services.daily_quotes_sync_service import DailyQuotesSyncService
from app.models.daily_quote import DailyQuote
from app.models.company import Company
from sqlalchemy import select, func, and_

# 認証ストラテジーを登録
from app.services.auth import StrategyRegistry
from app.services.auth.strategies.jquants_strategy import JQuantsStrategy
from app.services.auth.strategies.yfinance_strategy import YFinanceStrategy

# 認証ストラテジーを初期化
StrategyRegistry.register("jquants", JQuantsStrategy)
StrategyRegistry.register("yfinance", YFinanceStrategy)


async def test_jquants_connection():
    """J-Quants API接続テスト"""
    print("=== J-Quants API接続テスト ===")
    
    async with async_session_maker() as db:
        try:
            # サービスの初期化
            data_source_service = DataSourceService(db)
            client_manager = JQuantsClientManager(data_source_service)
            
            # J-QuantsデータソースID（マイグレーションで作成された）
            jquants_data_source_id = 1
            
            # クライアント取得
            print("1. J-Quants株価データクライアントを取得中...")
            client = await client_manager.get_daily_quotes_client(jquants_data_source_id)
            print("✓ クライアント取得成功")
            
            # 接続テスト
            print("2. J-Quants API接続テスト中...")
            connection_ok = await client.test_connection()
            if connection_ok:
                print("✓ J-Quants API接続成功")
            else:
                print("✗ J-Quants API接続失敗")
                return False
                
            return True
            
        except Exception as e:
            print(f"✗ エラー: {e}")
            return False


async def test_sample_data():
    """サンプル株価データ取得テスト"""
    print("\n=== サンプル株価データ取得テスト ===")
    
    async with async_session_maker() as db:
        try:
            # サービスの初期化
            data_source_service = DataSourceService(db)
            client_manager = JQuantsClientManager(data_source_service)
            client = await client_manager.get_daily_quotes_client(1)
            
            # 1. 特定銘柄の株価データを取得（トヨタ自動車: 72030）
            print("1. 特定企業（トヨタ自動車: 72030）の株価情報を取得中...")
            end_date = date.today()
            start_date = end_date - timedelta(days=7)
            
            quotes_data = await client.get_stock_prices_by_code(
                code="72030",
                from_date=start_date,
                to_date=end_date
            )
            
            if quotes_data:
                print("✓ 株価情報取得成功:")
                # 最新の株価データを表示
                latest_quote = quotes_data[-1]
                print(f"  - 取引日: {latest_quote.get('Date')}")
                print(f"  - 始値: {latest_quote.get('Open')}円")
                print(f"  - 高値: {latest_quote.get('High')}円")
                print(f"  - 安値: {latest_quote.get('Low')}円")
                print(f"  - 終値: {latest_quote.get('Close')}円")
                print(f"  - 出来高: {latest_quote.get('Volume'):,}株")
            else:
                print("✗ 株価データが見つかりませんでした")
            
            # 2. 特定日の全銘柄データ確認
            print("\n2. 特定日の全銘柄データ件数確認中...")
            # 最新の営業日を取得
            trade_date = end_date
            while trade_date.weekday() > 4:  # 土日をスキップ
                trade_date -= timedelta(days=1)
            
            daily_data = await client.get_stock_prices_by_date(trade_date)
            
            if daily_data:
                print(f"✓ {trade_date}の取得可能銘柄数: {len(daily_data)}件")
                print("サンプル銘柄（最初の3件）:")
                for i, quote in enumerate(daily_data[:3]):
                    print(f"  {i+1}. {quote.get('Code')} - 終値: {quote.get('Close')}円")
            else:
                print(f"✗ {trade_date}のデータが見つかりませんでした")
            
            return True
            
        except Exception as e:
            print(f"✗ エラー: {e}")
            import traceback
            traceback.print_exc()
            return False


async def test_daily_quotes_sync():
    """株価データ同期テスト"""
    print("\n=== 株価データ同期テスト ===")
    
    try:
        async with async_session_maker() as db:
            # サービスの初期化
            data_source_service = DataSourceService(db)
            client_manager = JQuantsClientManager(data_source_service)
            sync_service = DailyQuotesSyncService(data_source_service, client_manager)
        
        # 過去7日間のデータを同期
        end_date = date.today()
        start_date = end_date - timedelta(days=7)
        
        print(f"1. 株価データ同期を開始中...")
        print(f"   対象期間: {start_date} ~ {end_date}")
        print("   ※ 時間がかかる場合があります")
        
        sync_history = await sync_service.sync_daily_quotes(
            data_source_id=1,
            sync_type="full",
            from_date=start_date,
            to_date=end_date
        )
        
        if sync_history and sync_history.status == "completed":
            print("✓ 株価データ同期完了:")
            print(f"  - 同期ID: {sync_history.id}")
            print(f"  - 対象期間: {sync_history.start_date} ~ {sync_history.end_date}")
            print(f"  - ステータス: {sync_history.status}")
            print(f"  - 総レコード数: {sync_history.total_records}")
            print(f"  - 新規レコード数: {sync_history.new_records}")
            print(f"  - 更新レコード数: {sync_history.updated_records}")
            print(f"  - 開始時刻: {sync_history.started_at}")
            print(f"  - 完了時刻: {sync_history.completed_at}")
            return True
        else:
            print("✗ 同期に失敗しました")
            if sync_history:
                print(f"  - ステータス: {sync_history.status}")
                print(f"  - エラー: {sync_history.error_message}")
            return False
            
    except Exception as e:
        print(f"✗ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_database_search():
    """データベース検索テスト"""
    print("\n=== データベース検索テスト ===")
    
    async with async_session_maker() as db:
        try:
            # 1. 株価データ件数確認
            result = await db.execute(
                select(func.count(DailyQuote.id))
            )
            count = result.scalar()
            print(f"1. データベース内株価データ件数: {count:,}件")
            
            # 2. 最新の取引日を取得
            result = await db.execute(
                select(func.max(DailyQuote.trade_date))
            )
            latest_date = result.scalar()
            print(f"2. 最新取引日: {latest_date}")
            
            # 3. トヨタ自動車の最新株価を表示
            result = await db.execute(
                select(DailyQuote, Company)
                .join(Company, DailyQuote.code == Company.code)
                .where(Company.company_name.like('%トヨタ自動車%'))
                .order_by(DailyQuote.trade_date.desc())
                .limit(5)
            )
            quotes = result.all()
            
            if quotes:
                print("3. トヨタ自動車の最新株価（5日分）:")
                for quote, company in quotes:
                    print(f"  - {quote.trade_date}: 終値 {quote.close_price:,.0f}円 (出来高: {quote.volume:,}株)")
            else:
                print("3. トヨタ自動車の株価データが見つかりませんでした")
            
            # 4. 取引日別のデータ件数
            result = await db.execute(
                select(
                    DailyQuote.trade_date,
                    func.count(DailyQuote.id)
                )
                .group_by(DailyQuote.trade_date)
                .order_by(DailyQuote.trade_date.desc())
                .limit(5)
            )
            date_counts = result.all()
            
            if date_counts:
                print("\n4. 取引日別データ件数（最新5日）:")
                for trade_date, count in date_counts:
                    print(f"  - {trade_date}: {count:,}件")
            
            return True
            
        except Exception as e:
            print(f"✗ エラー: {e}")
            import traceback
            traceback.print_exc()
            return False


async def main():
    """メイン処理"""
    print("J-Quants API株価データ取得テストを開始します\n")
    
    # 各テストを実行
    tests = [
        ("API接続テスト", test_jquants_connection),
        ("サンプルデータ取得テスト", test_sample_data),
        ("株価データ同期テスト", test_daily_quotes_sync),
        ("データベース検索テスト", test_database_search),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n{test_name}でエラーが発生しました: {e}")
            results.append((test_name, False))
    
    # 結果サマリーを表示
    print("\n" + "="*50)
    print("テスト結果サマリー:")
    print("="*50)
    
    success_count = 0
    for test_name, result in results:
        status = "✓ 成功" if result else "✗ 失敗"
        print(f"{test_name}: {status}")
        if result:
            success_count += 1
    
    print(f"\n成功: {success_count}/{len(tests)}")
    
    return success_count == len(tests)


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nテストが中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n予期しないエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)