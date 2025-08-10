#!/usr/bin/env python
"""Docker 環境での Redis Sync 設定を診断するスクリプト"""
import os
import sys
import time
import json
import asyncio
import redis
import logging
from pathlib import Path
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


class RedisSyncDiagnostics:
    """Redis Sync 設定の診断クラス"""
    
    def __init__(self):
        self.results = {
            "environment_vars": {},
            "redis_connection": {},
            "pubsub_test": {},
            "celery_beat_config": {},
            "recommendations": []
        }
        
    def diagnose_environment_variables(self):
        """環境変数の確認"""
        logger.info("=" * 80)
        logger.info("環境変数の診断")
        logger.info("=" * 80)
        
        critical_vars = {
            "CELERY_BEAT_REDIS_SYNC_ENABLED": os.environ.get("CELERY_BEAT_REDIS_SYNC_ENABLED"),
            "CELERY_BEAT_MIN_SYNC_INTERVAL": os.environ.get("CELERY_BEAT_MIN_SYNC_INTERVAL"),
            "CELERY_BEAT_REDIS_CHANNEL": os.environ.get("CELERY_BEAT_REDIS_CHANNEL"),
            "REDIS_URL": os.environ.get("REDIS_URL"),
            "CELERY_BROKER_URL": os.environ.get("CELERY_BROKER_URL"),
        }
        
        for var_name, var_value in critical_vars.items():
            status = "✅" if var_value else "❌"
            logger.info(f"{status} {var_name}: {var_value or 'NOT SET'}")
            self.results["environment_vars"][var_name] = {
                "value": var_value,
                "is_set": bool(var_value)
            }
            
        # 設定クラスからの値も確認
        logger.info("\n 設定クラスからの値:")
        logger.info(f"  celery_beat_redis_sync_enabled: {settings.celery_beat_redis_sync_enabled}")
        logger.info(f"  celery_beat_min_sync_interval: {settings.celery_beat_min_sync_interval}")
        logger.info(f"  celery_beat_redis_channel: {settings.celery_beat_redis_channel}")
        
        self.results["environment_vars"]["from_settings"] = {
            "celery_beat_redis_sync_enabled": settings.celery_beat_redis_sync_enabled,
            "celery_beat_min_sync_interval": settings.celery_beat_min_sync_interval,
            "celery_beat_redis_channel": settings.celery_beat_redis_channel,
        }
        
        # 推奨事項
        if not critical_vars["CELERY_BEAT_REDIS_SYNC_ENABLED"]:
            self.results["recommendations"].append(
                "環境変数 CELERY_BEAT_REDIS_SYNC_ENABLED が設定されていません"
            )
            
    def test_redis_connection(self):
        """Redis 接続のテスト"""
        logger.info("\n" + "=" * 80)
        logger.info("Redis 接続テスト")
        logger.info("=" * 80)
        
        redis_urls = {
            "REDIS_URL": os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
            "CELERY_BROKER_URL": os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/1"),
        }
        
        for url_name, redis_url in redis_urls.items():
            try:
                logger.info(f"\n{url_name}: {redis_url}")
                client = redis.from_url(redis_url)
                
                # Ping テスト
                ping_result = client.ping()
                logger.info(f"  ✅ PING 応答: {ping_result}")
                
                # 書き込みテスト
                test_key = f"redis_sync_diag_{int(time.time())}"
                client.set(test_key, "test_value", ex=10)
                value = client.get(test_key)
                logger.info(f"  ✅ 書き込み/読み込みテスト: OK (値: {value})")
                
                # INFO 取得
                info = client.info()
                logger.info(f"  ✅ Redis バージョン: {info.get('redis_version', 'unknown')}")
                logger.info(f"  ✅ 接続クライアント数: {info.get('connected_clients', 'unknown')}")
                
                self.results["redis_connection"][url_name] = {
                    "status": "connected",
                    "ping": ping_result,
                    "version": info.get('redis_version', 'unknown'),
                    "connected_clients": info.get('connected_clients', 'unknown')
                }
                
            except Exception as e:
                logger.error(f"  ❌ 接続エラー: {e}")
                self.results["redis_connection"][url_name] = {
                    "status": "error",
                    "error": str(e)
                }
                self.results["recommendations"].append(
                    f"{url_name} への接続に失敗しました: {e}"
                )
                
    def test_pubsub(self):
        """Pub/Sub のテスト"""
        logger.info("\n" + "=" * 80)
        logger.info("Redis Pub/Sub テスト")
        logger.info("=" * 80)
        
        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        channel = settings.celery_beat_redis_channel
        
        try:
            # パブリッシャー
            pub_client = redis.from_url(redis_url)
            
            # サブスクライバー
            sub_client = redis.from_url(redis_url)
            pubsub = sub_client.pubsub()
            pubsub.subscribe(channel)
            
            logger.info(f"チャンネル '{channel}' にサブスクライブしました")
            
            # メッセージを受信するために少し待機
            time.sleep(0.5)
            
            # テストメッセージを送信
            test_message = {
                "event": "schedule_created",
                "schedule_id": "test_12345",
                "timestamp": time.time()
            }
            
            logger.info(f"テストメッセージを送信: {test_message}")
            pub_client.publish(channel, json.dumps(test_message))
            
            # メッセージを受信
            received = False
            for _ in range(10):  # 最大 1 秒待機
                message = pubsub.get_message(timeout=0.1)
                if message and message['type'] == 'message':
                    data = json.loads(message['data'])
                    logger.info(f"  ✅ メッセージ受信成功: {data}")
                    received = True
                    break
                    
            if received:
                self.results["pubsub_test"] = {
                    "status": "success",
                    "channel": channel,
                    "message_received": True
                }
            else:
                logger.error("  ❌ メッセージ受信タイムアウト")
                self.results["pubsub_test"] = {
                    "status": "timeout",
                    "channel": channel,
                    "message_received": False
                }
                self.results["recommendations"].append(
                    "Pub/Sub メッセージの受信に失敗しました。 Redis 設定を確認してください。"
                )
                
            pubsub.unsubscribe(channel)
            pubsub.close()
            
        except Exception as e:
            logger.error(f"  ❌ Pub/Sub テストエラー: {e}")
            self.results["pubsub_test"] = {
                "status": "error",
                "error": str(e)
            }
            self.results["recommendations"].append(
                f"Pub/Sub テストに失敗しました: {e}"
            )
            
    def check_celery_beat_config(self):
        """Celery Beat設定の確認"""
        logger.info("\n" + "=" * 80)
        logger.info("Celery Beat設定の確認")
        logger.info("=" * 80)
        
        # celery_configではなく、個別の変数をインポート
        from app.infrastructure.celery import config as celery_module
        
        beat_config = {
            "beat_scheduler": getattr(celery_module, 'beat_scheduler', 'NOT SET'),
            "beat_sync_every": getattr(celery_module, 'beat_sync_every', 'NOT SET'),
            "timezone": getattr(celery_module, 'timezone', 'NOT SET'),
        }
        
        for key, value in beat_config.items():
            logger.info(f"  {key}: {value}")
            
        self.results["celery_beat_config"] = beat_config
        
        # スケジューラーの確認
        expected_scheduler = "app.infrastructure.celery.schedulers.database_scheduler_asyncpg:DatabaseSchedulerAsyncPG"
        actual_scheduler = getattr(celery_module, 'beat_scheduler', None)
        if actual_scheduler != expected_scheduler:
            self.results["recommendations"].append(
                f"beat_schedulerが期待値と異なります。期待値: {expected_scheduler}, 実際: {actual_scheduler}"
            )
            
    def generate_summary(self):
        """診断結果のサマリー生成"""
        logger.info("\n" + "=" * 80)
        logger.info("診断結果サマリー")
        logger.info("=" * 80)
        
        # 問題の数をカウント
        env_issues = sum(1 for v in self.results["environment_vars"].values() 
                        if isinstance(v, dict) and not v.get("is_set", True))
        redis_issues = sum(1 for v in self.results["redis_connection"].values() 
                         if isinstance(v, dict) and v.get("status") != "connected")
        pubsub_ok = self.results["pubsub_test"].get("status") == "success"
        
        logger.info(f"\n 環境変数の問題: {env_issues}個")
        logger.info(f"Redis 接続の問題: {redis_issues}個")
        logger.info(f"Pub/Sub 動作: {'✅ 正常' if pubsub_ok else '❌ 異常'}")
        
        if self.results["recommendations"]:
            logger.info("\n📌 推奨事項:")
            for i, rec in enumerate(self.results["recommendations"], 1):
                logger.info(f"  {i}. {rec}")
        else:
            logger.info("\n✅ すべての診断項目が正常です")
            
        # 結果を JSON ファイルに保存
        output_file = Path(__file__).parent / "redis_sync_diagnosis.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        logger.info(f"\n 診断結果を保存しました: {output_file}")
        
    def run_diagnostics(self):
        """すべての診断を実行"""
        logger.info("Redis Sync 診断ツール")
        logger.info("=" * 80)
        
        try:
            self.diagnose_environment_variables()
            self.test_redis_connection()
            self.test_pubsub()
            self.check_celery_beat_config()
            self.generate_summary()
            
        except Exception as e:
            logger.error(f"\n 診断中にエラーが発生しました: {e}")
            import traceback
            traceback.print_exc()


def main():
    """メイン関数"""
    diagnostics = RedisSyncDiagnostics()
    diagnostics.run_diagnostics()


if __name__ == "__main__":
    main()