#!/usr/bin/env python3
"""TradesSpec 直接テストスクリプト（Celery を使わない）"""
import asyncio
import sys
from datetime import date, timedelta
from pathlib import Path

# プロジェクトのルートディレクトリを PYTHONPATH に追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.application.use_cases.fetch_trades_spec import FetchTradesSpecUseCase
from app.infrastructure.database.connection import get_async_session_context
from app.infrastructure.jquants.client_factory import JQuantsClientFactory
from app.infrastructure.repositories.database.trades_spec_repository_impl import TradesSpecRepositoryImpl


async def test_direct():
    """直接 API を呼び出してデータを取得・保存"""
    print("=== TradesSpec 直接テスト ===\n")
    
    try:
        # 日付範囲を設定
        to_date = date.today() - timedelta(days=1)
        from_date = to_date - timedelta(days=6)
        
        print(f"期間: {from_date} ~ {to_date}")
        print(f"市場区分: TSEPrime\n")
        
        # クライアントとリポジトリの準備
        factory = JQuantsClientFactory()
        client = await factory.create_trades_spec_client()
        
        async with get_async_session_context() as session:
            repository = TradesSpecRepositoryImpl(session)
            use_case = FetchTradesSpecUseCase(client, repository)
            
            # データ取得実行
            print("データ取得中...")
            result = await use_case.execute(
                section="TSEPrime",
                from_date=from_date,
                to_date=to_date,
                max_pages=1
            )
            
            print(f"\n 結果:")
            print(f"  成功: {result.success}")
            print(f"  取得件数: {result.fetched_count}")
            print(f"  保存件数: {result.saved_count}")
            
            if result.error_message:
                print(f"  エラー: {result.error_message}")
                
            # 保存されたデータを確認
            if result.saved_count > 0:
                print("\n 保存されたデータ:")
                saved_data = await repository.find_by_date_range_and_section(
                    from_date, to_date, "TSEPrime"
                )
                
                for spec in saved_data[:3]:  # 最初の 3 件のみ表示
                    print(f"  - {spec.code} ({spec.trade_date}): "
                          f"売買合計 {spec.sales_total:,}千円")
                    
            await session.commit()
            
    except Exception as e:
        print(f"\n✗ エラー発生: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_direct())