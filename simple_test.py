#!/usr/bin/env python3
"""
シンプルなJ-Quantsデータ取得テスト
"""

import asyncio
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.session import async_session_maker
from app.services.data_source_service import DataSourceService
from app.services.jquants_client import JQuantsClientManager

# 認証ストラテジーを登録
from app.services.auth import StrategyRegistry
from app.services.auth.strategies.jquants_strategy import JQuantsStrategy

StrategyRegistry.register("jquants", JQuantsStrategy)


async def test_basic_data_fetch():
    """基本的なデータ取得テスト"""
    try:
        async with async_session_maker() as db:
            # サービス初期化
            data_source_service = DataSourceService(db)
            client_manager = JQuantsClientManager(data_source_service)
            
            # クライアント取得
            client = await client_manager.get_client(1)
            
            # 数件のサンプルデータを取得
            print("J-Quants APIから少数のデータを取得中...")
            all_data = await client.get_all_listed_companies()
            
            print(f"取得件数: {len(all_data)}件")
            
            # 最初の5件を表示
            for i, company in enumerate(all_data[:5]):
                print(f"{i+1}. {company.get('Code')} - {company.get('CompanyName')}")
            
            return True
            
    except Exception as e:
        print(f"エラー: {e}")
        return False


async def test_specific_company():
    """特定企業のデータ取得テスト"""
    try:
        async with async_session_maker() as db:
            # サービス初期化
            data_source_service = DataSourceService(db)
            client_manager = JQuantsClientManager(data_source_service)
            
            # クライアント取得
            client = await client_manager.get_client(1)
            
            # トヨタ自動車の情報を取得
            print("トヨタ自動車(7203)の情報を取得中...")
            company_info = await client.get_company_info("7203")
            
            if company_info:
                print("取得成功:")
                print(f"  コード: {company_info.get('Code')}")
                print(f"  会社名: {company_info.get('CompanyName')}")
                print(f"  英語名: {company_info.get('CompanyNameEnglish')}")
                print(f"  市場: {company_info.get('MarketCodeName')}")
                print(f"  業種: {company_info.get('Sector17CodeName')}")
                return True
            else:
                print("取得失敗")
                return False
                
    except Exception as e:
        print(f"エラー: {e}")
        return False


async def main():
    """メイン関数"""
    print("=== シンプルなJ-Quantsテスト ===\n")
    
    print("1. 特定企業データ取得テスト")
    result1 = await test_specific_company()
    print(f"結果: {'成功' if result1 else '失敗'}\n")
    
    if result1:
        print("2. 全企業データ取得テスト（少数サンプル）")
        result2 = await test_basic_data_fetch()
        print(f"結果: {'成功' if result2 else '失敗'}")


if __name__ == "__main__":
    asyncio.run(main())