"""
CompanySyncServiceのパフォーマンステスト
"""

import asyncio
import time
from datetime import datetime, date
from unittest.mock import Mock, AsyncMock, patch
import pytest

from app.services.company_sync_service import CompanySyncService
from app.services.company_sync_service_v2 import CompanySyncServiceV2


@pytest.mark.asyncio
class TestCompanySyncPerformance:
    """CompanySyncServiceのパフォーマンステスト"""
    
    @pytest.fixture
    def mock_large_dataset(self):
        """大量のテストデータ"""
        return [
            {
                "Code": f"{i:04d}",
                "CompanyName": f"テスト会社{i}",
                "CompanyNameEnglish": f"Test Company {i}",
                "Sector17Code": str((i % 17) + 1),
                "Sector17CodeName": f"Sector {(i % 17) + 1}",
                "Sector33Code": str((i % 33) + 1),
                "Sector33CodeName": f"Sector {(i % 33) + 1}",
                "ScaleCategory": "TOPIX Large70" if i % 3 == 0 else "TOPIX Mid400",
                "MarketCode": "0111",
                "MarketCodeName": "プライム"
            }
            for i in range(1, 5001)  # 5000件のデータ
        ]
    
    @pytest.fixture
    def mock_services(self, mock_large_dataset):
        """モックサービスのセットアップ"""
        # データベースのモック
        db = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        db.add = Mock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()
        
        # データソースサービスのモック
        data_source_service = Mock()
        data_source_service.get_jquants_source = AsyncMock()
        mock_source = Mock()
        mock_source.id = 1
        data_source_service.get_jquants_source.return_value = mock_source
        
        # JQuantsクライアントマネージャーのモック
        jquants_client_manager = Mock()
        jquants_client_manager.get_client = AsyncMock()
        
        # クライアントのモック
        client = Mock()
        client.get_all_listed_companies = AsyncMock(return_value=mock_large_dataset)
        jquants_client_manager.get_client.return_value = client
        
        return db, data_source_service, jquants_client_manager
    
    async def test_sync_performance_v1_vs_v2(self, mock_services):
        """V1とV2のパフォーマンス比較"""
        db, data_source_service, jquants_client_manager = mock_services
        
        # V1のテスト
        service_v1 = CompanySyncService(db, data_source_service, jquants_client_manager)
        
        # 保存処理のモック（処理時間をシミュレート）
        async def mock_save_v1(data):
            await asyncio.sleep(0.001)  # 1msの遅延をシミュレート
            return {"new_count": len(data), "updated_count": 0}
        
        service_v1._save_companies_data = mock_save_v1
        service_v1.create_sync_history = AsyncMock()
        service_v1.update_sync_history_success = AsyncMock()
        
        start_time_v1 = time.time()
        try:
            await service_v1.sync_companies(
                data_source_id=1,
                sync_type="full"
            )
        except Exception:
            pass  # エラーは無視（パフォーマンス測定が目的）
        end_time_v1 = time.time()
        
        # V2のテスト
        service_v2 = CompanySyncServiceV2(db, data_source_service, jquants_client_manager)
        
        # リポジトリのモック
        async def mock_bulk_upsert(data):
            await asyncio.sleep(0.001)  # 1msの遅延をシミュレート
            return {"created": len(data), "updated": 0}
        
        mock_repository = Mock()
        mock_repository.bulk_upsert = AsyncMock(side_effect=mock_bulk_upsert)
        
        with patch.object(service_v2, '_initialize_repository', return_value=mock_repository):
            service_v2.create_sync_history = AsyncMock()
            service_v2.update_sync_history_success = AsyncMock()
            
            start_time_v2 = time.time()
            try:
                await service_v2.sync_companies(
                    data_source_id=1,
                    sync_type="full"
                )
            except Exception:
                pass  # エラーは無視（パフォーマンス測定が目的）
            end_time_v2 = time.time()
        
        # 結果を出力
        time_v1 = end_time_v1 - start_time_v1
        time_v2 = end_time_v2 - start_time_v2
        
        print(f"\n=== パフォーマンステスト結果 ===")
        print(f"データ件数: 5000件")
        print(f"V1処理時間: {time_v1:.3f}秒")
        print(f"V2処理時間: {time_v2:.3f}秒")
        print(f"差分: {abs(time_v2 - time_v1):.3f}秒")
        print(f"速度比: {time_v1/time_v2:.2f}倍")
        
        # V2がV1より大幅に遅くないことを確認（2倍以内）
        assert time_v2 < time_v1 * 2, f"V2が大幅に遅い: V1={time_v1:.3f}s, V2={time_v2:.3f}s"
    
    async def test_memory_efficiency(self, mock_services):
        """メモリ効率のテスト"""
        import psutil
        import os
        
        db, data_source_service, jquants_client_manager = mock_services
        
        # 現在のプロセスを取得
        process = psutil.Process(os.getpid())
        
        # V2のサービスを作成
        service_v2 = CompanySyncServiceV2(db, data_source_service, jquants_client_manager)
        
        # 初期メモリ使用量
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # リポジトリのモック
        mock_repository = Mock()
        mock_repository.bulk_upsert = AsyncMock(return_value={"created": 5000, "updated": 0})
        
        with patch.object(service_v2, '_initialize_repository', return_value=mock_repository):
            service_v2.create_sync_history = AsyncMock()
            service_v2.update_sync_history_success = AsyncMock()
            
            # 10回実行してメモリリークがないか確認
            for i in range(10):
                try:
                    await service_v2.sync_companies(
                        data_source_id=1,
                        sync_type="full"
                    )
                except Exception:
                    pass
                
                # 各実行後のメモリ使用量
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = current_memory - initial_memory
                
                print(f"実行 {i+1}: メモリ使用量 {current_memory:.1f}MB (増加: +{memory_increase:.1f}MB)")
        
        # 最終メモリ使用量
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        total_increase = final_memory - initial_memory
        
        print(f"\n=== メモリ効率テスト結果 ===")
        print(f"初期メモリ: {initial_memory:.1f}MB")
        print(f"最終メモリ: {final_memory:.1f}MB")
        print(f"総増加量: {total_increase:.1f}MB")
        
        # メモリリークがないことを確認（100MB以内の増加）
        assert total_increase < 100, f"メモリ使用量が大幅に増加: {total_increase:.1f}MB"
    
    async def test_batch_processing_performance(self, mock_services):
        """バッチ処理のパフォーマンステスト"""
        db, data_source_service, jquants_client_manager = mock_services
        
        service_v2 = CompanySyncServiceV2(db, data_source_service, jquants_client_manager)
        
        # 異なるバッチサイズでのテスト
        batch_sizes = [100, 500, 1000, 2000]
        results = []
        
        for batch_size in batch_sizes:
            # バッチサイズを設定
            service_v2._batch_size = batch_size
            
            # リポジトリのモック
            mock_repository = Mock()
            call_count = 0
            async def mock_bulk_upsert(data):
                nonlocal call_count
                call_count += 1
                await asyncio.sleep(0.01)  # 10msの遅延
                return {"created": len(data), "updated": 0}
            
            mock_repository.bulk_upsert = AsyncMock(side_effect=mock_bulk_upsert)
            
            with patch.object(service_v2, '_initialize_repository', return_value=mock_repository):
                service_v2.create_sync_history = AsyncMock()
                service_v2.update_sync_history_success = AsyncMock()
                
                start_time = time.time()
                try:
                    await service_v2.sync_companies(
                        data_source_id=1,
                        sync_type="full"
                    )
                except Exception:
                    pass
                end_time = time.time()
                
                results.append({
                    "batch_size": batch_size,
                    "time": end_time - start_time,
                    "calls": call_count
                })
        
        print("\n=== バッチ処理パフォーマンステスト結果 ===")
        for result in results:
            print(f"バッチサイズ: {result['batch_size']:4d} - "
                  f"処理時間: {result['time']:.3f}秒 - "
                  f"DB呼び出し回数: {result['calls']}")
        
        # バッチサイズが大きいほど効率的であることを確認
        assert results[-1]['time'] < results[0]['time'], "バッチサイズ増加による効率化が見られない"