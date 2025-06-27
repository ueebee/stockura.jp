#!/usr/bin/env python3
"""
J-Quants API上場情報データ取得テストスクリプト
"""

import asyncio
import sys
import os
from datetime import datetime
import datetime as dt

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.session import async_session_maker
from app.services.data_source_service import DataSourceService
from app.services.jquants_client import JQuantsClientManager
from app.services.company_sync_service import CompanySyncService

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
            print("1. J-Quantsクライアントを取得中...")
            client = await client_manager.get_client(jquants_data_source_id)
            print("✓ クライアント取得成功")
            
            # 接続テスト
            print("2. J-Quants API接続テスト中...")
            connection_ok = await client.test_connection()
            
            if connection_ok:
                print("✓ J-Quants API接続成功")
                return True
            else:
                print("✗ J-Quants API接続失敗")
                return False
                
        except Exception as e:
            print(f"✗ 接続テストエラー: {e}")
            return False


async def test_get_sample_data():
    """サンプルデータ取得テスト"""
    print("\n=== サンプルデータ取得テスト ===")
    
    async with async_session_maker() as db:
        try:
            # サービスの初期化
            data_source_service = DataSourceService(db)
            client_manager = JQuantsClientManager(data_source_service)
            
            # J-QuantsデータソースID
            jquants_data_source_id = 1
            
            # クライアント取得
            client = await client_manager.get_client(jquants_data_source_id)
            
            # 特定企業の情報を取得（トヨタ自動車: 7203）
            print("1. 特定企業（トヨタ自動車: 7203）の情報を取得中...")
            company_info = await client.get_company_info("7203")
            
            if company_info:
                print("✓ 企業情報取得成功:")
                print(f"  - コード: {company_info.get('Code')}")
                print(f"  - 会社名: {company_info.get('CompanyName')}")
                print(f"  - 英語名: {company_info.get('CompanyNameEnglish')}")
                print(f"  - 市場: {company_info.get('MarketCodeName')}")
                print(f"  - 業種: {company_info.get('Sector17CodeName')}")
            else:
                print("✗ 企業情報が取得できませんでした")
                return False
            
            # 全企業データの一部を取得（件数確認のため）
            print("\n2. 全企業データの件数確認中...")
            all_companies = await client.get_all_listed_companies()
            print(f"✓ 取得可能企業数: {len(all_companies)}件")
            
            if len(all_companies) > 0:
                print("サンプル企業（最初の3件）:")
                for i, company in enumerate(all_companies[:3]):
                    print(f"  {i+1}. {company.get('Code')} - {company.get('CompanyName')}")
            
            return True
            
        except Exception as e:
            print(f"✗ データ取得エラー: {e}")
            return False


async def test_company_sync():
    """企業データ同期テスト"""
    print("\n=== 企業データ同期テスト ===")
    
    async with async_session_maker() as db:
        try:
            # サービスの初期化
            data_source_service = DataSourceService(db)
            client_manager = JQuantsClientManager(data_source_service)
            sync_service = CompanySyncService(db, data_source_service, client_manager)
            
            # J-QuantsデータソースID
            jquants_data_source_id = 1
            
            print("1. 企業データ同期を開始中...")
            print("   ※ 初回は時間がかかる場合があります")
            
            # 同期実行
            sync_history = await sync_service.sync_companies(
                data_source_id=jquants_data_source_id,
                sync_date=dt.date.today(),
                sync_type="full"
            )
            
            print("✓ 企業データ同期完了:")
            print(f"  - 同期ID: {sync_history.id}")
            print(f"  - 同期日: {sync_history.sync_date}")
            print(f"  - ステータス: {sync_history.status}")
            print(f"  - 総企業数: {sync_history.total_companies}")
            print(f"  - 新規企業数: {sync_history.new_companies}")
            print(f"  - 更新企業数: {sync_history.updated_companies}")
            print(f"  - 開始時刻: {sync_history.started_at}")
            print(f"  - 完了時刻: {sync_history.completed_at}")
            
            if sync_history.error_message:
                print(f"  - エラー: {sync_history.error_message}")
            
            return sync_history.status == "completed"
            
        except Exception as e:
            print(f"✗ 同期エラー: {e}")
            return False


async def test_database_query():
    """データベース検索テスト"""
    print("\n=== データベース検索テスト ===")
    
    async with async_session_maker() as db:
        try:
            from sqlalchemy import select, func
            from app.models.company import Company
            
            # 企業数の確認
            result = await db.execute(select(func.count(Company.id)))
            total_companies = result.scalar()
            print(f"1. データベース内企業数: {total_companies}件")
            
            if total_companies > 0:
                # サンプル企業を表示
                result = await db.execute(
                    select(Company).limit(5).order_by(Company.code)
                )
                companies = result.scalars().all()
                
                print("2. サンプル企業一覧:")
                for company in companies:
                    print(f"  - {company.code}: {company.company_name} ({company.market_code})")
                
                # 特定の検索テスト
                result = await db.execute(
                    select(Company).where(Company.code == "7203")
                )
                toyota = result.scalar_one_or_none()
                
                if toyota:
                    print(f"\n3. トヨタ自動車検索結果:")
                    print(f"  - コード: {toyota.code}")
                    print(f"  - 会社名: {toyota.company_name}")
                    print(f"  - 英語名: {toyota.company_name_english}")
                    print(f"  - 業種17: {toyota.sector17_code}")
                    print(f"  - 市場: {toyota.market_code}")
                    print(f"  - 基準日: {toyota.reference_date}")
                else:
                    print("3. トヨタ自動車が見つかりませんでした")
            
            return True
            
        except Exception as e:
            print(f"✗ データベース検索エラー: {e}")
            return False


async def main():
    """メイン関数"""
    print("J-Quants APIデータ取得テストを開始します\n")
    
    # テスト実行
    tests = [
        ("API接続テスト", test_jquants_connection),
        ("サンプルデータ取得テスト", test_get_sample_data),
        ("企業データ同期テスト", test_company_sync),
        ("データベース検索テスト", test_database_query),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
            
            # 失敗したら後続テストをスキップ
            if not result and test_name != "データベース検索テスト":
                print(f"\n{test_name}が失敗したため、後続テストをスキップします。")
                break
                
        except Exception as e:
            print(f"\n✗ {test_name}で予期せぬエラー: {e}")
            results.append((test_name, False))
            break
    
    # 結果サマリー
    print("\n" + "="*50)
    print("テスト結果サマリー:")
    print("="*50)
    
    for test_name, result in results:
        status = "✓ 成功" if result else "✗ 失敗"
        print(f"{test_name}: {status}")
    
    success_count = sum(1 for _, result in results if result)
    total_count = len(results)
    print(f"\n成功: {success_count}/{total_count}")


if __name__ == "__main__":
    # イベントループで実行
    asyncio.run(main())