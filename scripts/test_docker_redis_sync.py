#!/usr/bin/env python
"""Docker 環境での Redis Sync 機能の統合テスト"""
import os
import sys
import time
import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# プロジェクトのルートディレクトリを Python パスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime) s] %(levelname) s: %(message) s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class DockerRedisSyncTest:
    """Docker 環境での Redis Sync 統合テスト"""
    
    def __init__(self):
        self.test_results = {
            "diagnosis": {},
            "schedule_creation": {},
            "event_verification": {},
            "execution_history": {},
            "overall_status": "pending"
        }
        
    async def run_diagnosis(self):
        """診断スクリプトを実行"""
        logger.info("=" * 80)
        logger.info("1. 診断スクリプトの実行")
        logger.info("=" * 80)
        
        try:
            # 診断スクリプトを実行
            import subprocess
            result = subprocess.run(
                ["docker", "compose", "exec", "-T", "app", "python", "scripts/diagnose_redis_sync_docker.py"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info("✅ 診断スクリプトが正常に完了しました")
                
                # 診断結果の JSON ファイルを読み込む
                diagnosis_file = Path(__file__).parent / "redis_sync_diagnosis.json"
                if diagnosis_file.exists():
                    with open(diagnosis_file, 'r', encoding='utf-8') as f:
                        diagnosis_data = json.load(f)
                        
                    # 結果を解析
                    env_ok = all(
                        v.get("is_set", False) 
                        for k, v in diagnosis_data["environment_vars"].items() 
                        if isinstance(v, dict) and k.startswith("CELERY_BEAT_REDIS_SYNC")
                    )
                    redis_ok = all(
                        v.get("status") == "connected" 
                        for v in diagnosis_data["redis_connection"].values()
                        if isinstance(v, dict)
                    )
                    pubsub_ok = diagnosis_data["pubsub_test"].get("status") == "success"
                    
                    self.test_results["diagnosis"] = {
                        "status": "success",
                        "environment_vars_ok": env_ok,
                        "redis_connection_ok": redis_ok,
                        "pubsub_ok": pubsub_ok
                    }
                    
                    logger.info(f"  環境変数: {'✅' if env_ok else '❌'}")
                    logger.info(f"  Redis 接続: {'✅' if redis_ok else '❌'}")
                    logger.info(f"  Pub/Sub: {'✅' if pubsub_ok else '❌'}")
                else:
                    logger.warning("診断結果ファイルが見つかりません")
                    self.test_results["diagnosis"]["status"] = "warning"
            else:
                logger.error(f"診断スクリプトエラー: {result.stderr}")
                self.test_results["diagnosis"]["status"] = "error"
                
        except Exception as e:
            logger.error(f"診断実行エラー: {e}")
            self.test_results["diagnosis"]["status"] = "error"
            
    async def test_schedule_creation_and_event(self):
        """スケジュール作成とイベント発行のテスト"""
        logger.info("\n" + "=" * 80)
        logger.info("2. スケジュール作成とイベント確認")
        logger.info("=" * 80)
        
        try:
            import aiohttp
            
            # API エンドポイント
            api_base = os.environ.get("API_BASE", "http://localhost:8000")
            url = f"{api_base}/api/v1/schedules"
            
            # テスト用スケジュールデータ
            schedule_data = {
                "name": f"redis_sync_test_{int(time.time())}",
                "task_name": "fetch_listed_info_task",
                "cron_expression": "0 0 * * *",  # 毎日 0 時
                "description": "Redis Sync 統合テスト",
                "enabled": True,
                "task_params": {
                    "period_type": "custom",
                    "from_date": "2024-08-06",
                    "to_date": "2024-08-06"
                }
            }
            
            # Redis イベントモニターを起動
            monitor_process = await asyncio.create_subprocess_exec(
                "docker", "compose", "exec", "-T", "app", "python", "scripts/monitor_redis_events.py",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # 少し待機してモニターを準備
            await asyncio.sleep(2)
            
            # スケジュールを作成
            logger.info("スケジュール作成中...")
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
                        
                        # モニタープロセスを終了
                        monitor_process.terminate()
                        await monitor_process.wait()
                        
                        # モニターの出力を確認
                        stdout, stderr = await monitor_process.communicate()
                        output = stdout.decode('utf-8')
                        
                        if "schedule_created" in output and schedule_id in output:
                            logger.info("✅ Redis イベントの発行を確認")
                            self.test_results["event_verification"] = {
                                "status": "success",
                                "event_received": True
                            }
                        else:
                            logger.warning("❌ Redis イベントが確認できません")
                            self.test_results["event_verification"] = {
                                "status": "failure",
                                "event_received": False
                            }
                            
                        # クリーンアップ：スケジュールを削除
                        delete_url = f"{url}/{schedule_id}"
                        async with session.delete(delete_url) as del_response:
                            if del_response.status == 204:
                                logger.info("✅ テストスケジュールを削除しました")
                    else:
                        error_text = await response.text()
                        logger.error(f"スケジュール作成エラー: {error_text}")
                        self.test_results["schedule_creation"]["status"] = "error"
                        
        except Exception as e:
            logger.error(f"テストエラー: {e}")
            self.test_results["schedule_creation"]["status"] = "error"
            self.test_results["event_verification"]["status"] = "error"
            
    async def check_celery_beat_logs(self):
        """Celery Beat のログを確認"""
        logger.info("\n" + "=" * 80)
        logger.info("3. Celery Beat ログの確認")
        logger.info("=" * 80)
        
        try:
            import subprocess
            
            # Celery Beat のログを取得
            result = subprocess.run(
                ["docker", "compose", "logs", "celery-beat", "--tail=50"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logs = result.stdout
                
                # 重要なログメッセージを確認
                critical_messages = {
                    "Redis Sync is ENABLED": False,
                    "Redis subscriber thread started": False,
                    "Subscribed to Redis channel": False,
                    "Received schedule event": False,
                    "Triggering immediate schedule sync": False
                }
                
                for message in critical_messages:
                    if message in logs:
                        critical_messages[message] = True
                        logger.info(f"✅ '{message}' が確認されました")
                    else:
                        logger.warning(f"❌ '{message}' が見つかりません")
                        
                # 結果を記録
                all_ok = all(critical_messages.values())
                self.test_results["celery_beat_logs"] = {
                    "status": "success" if all_ok else "partial",
                    "messages_found": critical_messages
                }
                
                if not all_ok:
                    logger.info("\n 最新の Celery Beat ログ（抜粋）:")
                    logger.info("-" * 40)
                    for line in logs.split('\n')[-20:]:
                        if any(keyword in line for keyword in ["Redis", "sync", "schedule", "CELERY"]):
                            logger.info(f"  {line}")
            else:
                logger.error("Celery Beat ログの取得に失敗しました")
                self.test_results["celery_beat_logs"] = {"status": "error"}
                
        except Exception as e:
            logger.error(f"ログ確認エラー: {e}")
            self.test_results["celery_beat_logs"] = {"status": "error"}
            
    def generate_summary(self):
        """テスト結果のサマリーを生成"""
        logger.info("\n" + "=" * 80)
        logger.info("テスト結果サマリー")
        logger.info("=" * 80)
        
        # 各テストの結果を確認
        all_success = True
        
        for test_name, result in self.test_results.items():
            if test_name == "overall_status":
                continue
                
            if isinstance(result, dict) and result.get("status") == "success":
                logger.info(f"✅ {test_name}: 成功")
            else:
                logger.warning(f"❌ {test_name}: 失敗または警告")
                all_success = False
                
        self.test_results["overall_status"] = "success" if all_success else "failure"
        
        # 結果をファイルに保存
        output_file = Path(__file__).parent / "docker_redis_sync_test_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
            
        logger.info(f"\n テスト結果を保存しました: {output_file}")
        
        if all_success:
            logger.info("\n🎉 すべてのテストが成功しました！")
        else:
            logger.warning("\n⚠️  一部のテストが失敗しました。詳細を確認してください。")
            
    async def run_all_tests(self):
        """すべてのテストを実行"""
        logger.info("Docker Redis Sync 統合テスト")
        logger.info("=" * 80)
        
        try:
            # 1. 診断を実行
            await self.run_diagnosis()
            
            # 2. スケジュール作成とイベント確認
            await self.test_schedule_creation_and_event()
            
            # 3. Celery Beat ログ確認
            await self.check_celery_beat_logs()
            
            # 4. サマリー生成
            self.generate_summary()
            
        except Exception as e:
            logger.error(f"テスト実行中にエラーが発生しました: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """メイン関数"""
    tester = DockerRedisSyncTest()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())