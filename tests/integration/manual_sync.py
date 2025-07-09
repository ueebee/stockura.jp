import asyncio
from datetime import date
from app.db.session import async_session_maker
from app.services.data_source_service import DataSourceService
from app.services.jquants_client import JQuantsClientManager
from app.services.company_sync_service import CompanySyncService

# 認証ストラテジーを登録
from app.services.auth import StrategyRegistry
from app.services.auth.strategies.jquants_strategy import JQuantsStrategy
StrategyRegistry.register("jquants", JQuantsStrategy)

async def manual_sync():
    async with async_session_maker() as db:
        # サービス初期化
        data_source_service = DataSourceService(db)
        client_manager = JQuantsClientManager(data_source_service)
        sync_service = CompanySyncService(db, data_source_service, client_manager)
        
        # 同期実行（J-QuantsデータソースID: 1）
        sync_history = await sync_service.sync_companies(
            data_source_id=1,
            sync_type="full"
        )
        
        print(f"同期完了 - ステータス: {sync_history.status}")
        print(f"総企業数: {sync_history.total_companies}")
        print(f"新規: {sync_history.new_companies}, 更新: {sync_history.updated_companies}")

# 実行
asyncio.run(manual_sync())
