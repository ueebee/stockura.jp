#!/usr/bin/env python
"""コンテナ内部から実行する Redis Sync 機能のテスト"""
import os
import sys
import time
import asyncio
import json
import logging
import redis
import aiohttp
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# プロジェクトのルートディレクトリを Python パスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime) s] %(levelname) s: %(message) s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class InternalRedisSyncTest:
    """コンテナ内部での Redis Sync 統合テスト"""
    
    def __init__(self):
        self.test_results = {
            "redis_connection": {},
            "pubsub_test": {},
            "schedule_creation": {},
            "event_monitoring": {},
            "overall_status": "pending"
        }
        
    async def test_redis_connection(self):
        """Redis 接続のテスト"""
        logger.info("=" * 80)
        logger.info("1. Redis 接続テスト")
        logger.info("=" * 80)
        
        try:
            # Redis 接続
            client = redis.Redis.from_url(settings.redis_url)
            
            # Ping テスト
            ping_result = client.ping()
            logger.info(f"✅ Redis PING: {ping_result}")
            
            # 書き込み/読み込みテスト
            test_key = f"internal_test_{int(time.time())}"
            client.set(test_key, "test_value", ex=10)
            value = client.get(test_key)
            logger.info(f"✅ 書き込み/読み込み: OK (値: {value})")
            
            self.test_results["redis_connection"] = {
                "status": "success",
                "ping": ping_result
            }
            
        except Exception as e:
            logger.error(f"❌ Redis 接続エラー: {e}")
            self.test_results["redis_connection"] = {
                "status": "error",
                "error": str(e)
            }
            
    async def test_pubsub(self):
        """Pub/Sub のテスト"""
        logger.info("\n" + "=" * 80)
        logger.info("2. Redis Pub/Sub テスト")
        logger.info("=" * 80)
        
        try:
            # パブリッシャー
            pub_client = redis.Redis.from_url(settings.redis_url)
            
            # サブスクライバー
            sub_client = redis.Redis.from_url(settings.redis_url)
            pubsub = sub_client.pubsub()
            pubsub.subscribe(settings.celery_beat_redis_channel)
            
            logger.info(f"チャンネル '{settings.celery_beat_redis_channel}' にサブスクライブ")
            
            # 少し待機
            await asyncio.sleep(0.5)
            
            # テストメッセージ送信
            test_message = {
                "event_type": "test_event",
                "schedule_id": "test_internal_123",
                "timestamp": time.time()
            }
            
            pub_client.publish(
                settings.celery_beat_redis_channel, 
                json.dumps(test_message)
            )
            logger.info(f"テストメッセージ送信: {test_message}")
            
            # メッセージ受信
            received = False
            for _ in range(10):
                message = pubsub.get_message(timeout=0.1)
                if message and message['type'] == 'message':
                    data = json.loads(message['data'])
                    logger.info(f"✅ メッセージ受信: {data}")
                    received = True
                    break
                    
            self.test_results["pubsub_test"] = {
                "status": "success" if received else "timeout",
                "message_received": received
            }
            
            pubsub.unsubscribe(settings.celery_beat_redis_channel)
            pubsub.close()
            
        except Exception as e:
            logger.error(f"❌ Pub/Sub エラー: {e}")
            self.test_results["pubsub_test"] = {
                "status": "error",
                "error": str(e)
            }
            
    async def test_schedule_api(self):
        """スケジュール API 経由でのテスト"""
        logger.info("\n" + "=" * 80)
        logger.info("3. スケジュール API テスト")
        logger.info("=" * 80)
        
        try:
            # API エンドポイント（コンテナ内部なので localhost を使用）
            api_base = "http://localhost:8000"
            url = f"{api_base}/api/v1/schedules"
            
            # テスト用スケジュール
            schedule_data = {
                "name": f"internal_test_{int(time.time())}",
                "task_name": "fetch_listed_info_task",
                "cron_expression": "0 0 * * *",
                "description": "内部テスト",
                "enabled": True,
                "task_params": {
                    "period_type": "custom",
                    "from_date": "2024-08-06",
                    "to_date": "2024-08-06"
                }
            }
            
            # Redis イベントを監視するタスクを開始
            monitor_task = asyncio.create_task(self.monitor_redis_events())
            
            # スケジュール作成
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=schedule_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        schedule_id = result["id"]
                        logger.info(f"✅ スケジュール作成成功 (ID: {schedule_id})")
                        
                        self.test_results["schedule_creation"] = {
                            "status": "success",
                            "schedule_id": schedule_id
                        }
                        
                        # イベントが発行されるまで待機
                        await asyncio.sleep(3)
                        
                        # モニタータスクをキャンセル
                        monitor_task.cancel()
                        try:
                            await monitor_task
                        except asyncio.CancelledError:
                            pass
                        
                        # クリーンアップ
                        delete_url = f"{url}/{schedule_id}"
                        async with session.delete(delete_url) as del_response:
                            if del_response.status == 204:
                                logger.info("✅ テストスケジュールを削除")
                    else:
                        error_text = await response.text()
                        logger.error(f"スケジュール作成エラー: {error_text}")
                        self.test_results["schedule_creation"]["status"] = "error"
                        
        except Exception as e:
            logger.error(f"❌ API テストエラー: {e}")
            self.test_results["schedule_creation"]["status"] = "error"
            
    async def monitor_redis_events(self):
        """Redis イベントを監視"""
        try:
            client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
            pubsub = client.pubsub()
            pubsub.subscribe(settings.celery_beat_redis_channel)
            
            event_received = False
            
            while not event_received:
                message = pubsub.get_message(timeout=0.1)
                if message and message['type'] == 'message':
                    try:
                        data = json.loads(message['data'])
                        if data.get('event_type') == 'schedule_created':
                            logger.info(f"🔔 スケジュール作成イベントを検出: {data}")
                            self.test_results["event_monitoring"] = {
                                "status": "success",
                                "event_detected": True,
                                "event_data": data
                            }
                            event_received = True
                    except json.JSONDecodeError:
                        pass
                        
                await asyncio.sleep(0.1)
                
        except asyncio.CancelledError:
            if not event_received:
                self.test_results["event_monitoring"] = {
                    "status": "timeout",
                    "event_detected": False
                }
        except Exception as e:
            logger.error(f"モニタリングエラー: {e}")
            self.test_results["event_monitoring"] = {
                "status": "error",
                "error": str(e)
            }
            
    def generate_summary(self):
        """テスト結果のサマリー"""
        logger.info("\n" + "=" * 80)
        logger.info("テスト結果サマリー")
        logger.info("=" * 80)
        
        all_success = True
        
        for test_name, result in self.test_results.items():
            if test_name == "overall_status":
                continue
                
            if isinstance(result, dict) and result.get("status") == "success":
                logger.info(f"✅ {test_name}: 成功")
            else:
                logger.warning(f"❌ {test_name}: 失敗")
                all_success = False
                
        self.test_results["overall_status"] = "success" if all_success else "failure"
        
        # 結果を保存
        output_file = Path(__file__).parent / "internal_redis_sync_test_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
            
        logger.info(f"\n テスト結果を保存: {output_file}")
        
        if all_success:
            logger.info("\n🎉 すべてのテストが成功しました！")
        else:
            logger.warning("\n⚠️ 一部のテストが失敗しました")
            
    async def run_all_tests(self):
        """すべてのテストを実行"""
        logger.info("内部 Redis Sync 統合テスト")
        logger.info("=" * 80)
        
        try:
            await self.test_redis_connection()
            await self.test_pubsub()
            await self.test_schedule_api()
            self.generate_summary()
            
        except Exception as e:
            logger.error(f"テスト実行エラー: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """メイン関数"""
    tester = InternalRedisSyncTest()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())