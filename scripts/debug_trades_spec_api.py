#!/usr/bin/env python3
"""TradesSpec API のデバッグスクリプト"""
import asyncio
import json
import sys
from datetime import date, timedelta
from pathlib import Path

# プロジェクトのルートディレクトリを PYTHONPATH に追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.infrastructure.jquants.client_factory import JQuantsClientFactory


async def debug_trades_spec_api():
    """J-Quants API から直接データを取得してデバッグ"""
    print("=== TradesSpec API デバッグ ===\n")
    
    try:
        # JQuantsClientFactory を初期化
        factory = JQuantsClientFactory()
        
        # 認証
        print("1. J-Quants API 認証中...")
        await factory._ensure_authenticated()
        print("✓ 認証成功\n")
        
        # TradesSpecClient を作成
        client = await factory.create_trades_spec_client()
        
        # 日付範囲を設定（昨日から 7 日前まで）
        to_date = date.today() - timedelta(days=1)
        from_date = to_date - timedelta(days=6)
        
        print(f"2. データ取得テスト")
        print(f"   期間: {from_date} ~ {to_date}")
        print(f"   市場区分: TSEPrime\n")
        
        # API を直接呼び出し（ページネーションなし）
        print("3. API レスポンス (直接呼び出し):")
        response = await client.fetch_trades_spec(
            section="TSEPrime",
            from_date=from_date,
            to_date=to_date
        )
        
        print(f"   レスポンスキー: {list(response.keys())}")
        
        if "trades_spec" in response:
            data = response["trades_spec"]
            print(f"   データ件数: {len(data)}件")
            
            if data:
                print("\n   最初のレコード:")
                print(json.dumps(data[0], indent=2, ensure_ascii=False))
                
                # データ構造を確認
                first_record = data[0]
                print("\n   利用可能なフィールド:")
                for key in sorted(first_record.keys()):
                    print(f"     - {key}: {type(first_record[key]).__name__}")
        else:
            print(f"   'trades_spec'キーが見つかりません。実際のレスポンス:")
            print(json.dumps(response, indent=2, ensure_ascii=False))
            
        # ページネーション対応版のテスト
        print("\n4. ページネーション対応版のテスト:")
        all_data = await client.fetch_all_trades_spec(
            section="TSEPrime",
            from_date=from_date,
            to_date=to_date,
            max_pages=1
        )
        
        print(f"   取得されたエンティティ数: {len(all_data)}件")
        
        if all_data:
            print("\n   最初のエンティティ:")
            first_entity = all_data[0]
            print(f"     - code: {first_entity.code}")
            print(f"     - trade_date: {first_entity.trade_date}")
            print(f"     - section: {first_entity.section}")
            print(f"     - sales_total: {first_entity.sales_total}")
            print(f"     - purchases_total: {first_entity.purchases_total}")
            print(f"     - balance_total: {first_entity.balance_total}")
            
        # 異なる市場区分でのテスト
        print("\n5. 他の市場区分でのテスト:")
        for section in ["TSEStandard", "TSEGrowth"]:
            response = await client.fetch_trades_spec(
                section=section,
                from_date=to_date,
                to_date=to_date
            )
            
            data_count = len(response.get("trades_spec", []))
            print(f"   {section}: {data_count}件")
            
        # 市場区分を指定しない場合
        print("\n6. 市場区分を指定しない場合:")
        response = await client.fetch_trades_spec(
            from_date=to_date,
            to_date=to_date
        )
        
        data_count = len(response.get("trades_spec", []))
        print(f"   全市場: {data_count}件")
        
        if response.get("trades_spec"):
            sections = set(item.get("Section", "N/A") for item in response["trades_spec"])
            print(f"   含まれる市場区分: {', '.join(sorted(sections))}")
            
    except Exception as e:
        print(f"\n✗ エラー発生: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_trades_spec_api())