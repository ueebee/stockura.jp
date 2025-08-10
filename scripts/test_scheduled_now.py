#!/usr/bin/env python
"""1 分以内に実行されるスケジュールを作成するテストスクリプト"""
import os
import sys
import time
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple, List
import requests

# プロジェクトのルートディレクトリを Python パスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime) s] %(levelname) s: %(message) s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class ScheduledNowTester:
    """1 分以内に実行されるスケジュールのテスト"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"
        self.created_schedule_ids: List[str] = []
        
    def create_schedule_for_next_minute(self) -> Dict:
        """次の分に実行されるスケジュールを作成"""
        url = f"{self.api_base}/schedules"
        
        # 現在時刻の次の分を計算
        now = datetime.now()
        next_minute = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
        
        # cron 式を生成
        cron_expression = f"{next_minute.minute} {next_minute.hour} * * *"
        
        logger.info(f"現在時刻: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"実行予定: {next_minute.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"cron 式: {cron_expression}")
        
        request_data = {
            "name": f"test_now_{int(time.time())}",
            "task_name": "fetch_listed_info_task",
            "cron_expression": cron_expression,
            "description": "1 分以内実行テスト",
            "enabled": True,
            "task_params": {
                "period_type": "custom",
                "from_date": "2024-08-06",
                "to_date": "2024-08-06",
                "codes": None,
                "market": None
            }
        }
        
        logger.info("\n スケジュール作成中...")
        
        try:
            response = requests.post(url, json=request_data, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            self.created_schedule_ids.append(result["id"])
            
            logger.info(f"✅ スケジュール作成成功")
            logger.info(f"  ID: {result['id']}")
            logger.info(f"  名前: {result['name']}")
            
            # 実行までの秒数を計算
            wait_seconds = (next_minute - datetime.now()).total_seconds()
            logger.info(f"\n⏱️ 実行まで約 {int(wait_seconds)} 秒")
            
            return result
        except Exception as e:
            logger.error(f"スケジュール作成エラー: {e}")
            raise
            
    def monitor_celery_beat(self):
        """Celery Beat のログをモニタリング（表示のみ）"""
        logger.info("\nCelery Beat のログを確認するには別ターミナルで:")
        logger.info("docker compose logs -f celery-beat | grep -E 'test_now|Sending|task|executed'")
        
    def monitor_execution(self, schedule_id: str, timeout: int = 120):
        """スケジュールの実行を監視"""
        logger.info("\n 実行履歴を監視中...")
        
        start_time = time.time()
        check_interval = 5
        last_status_check = 0
        
        while time.time() - start_time < timeout:
            try:
                # 実行履歴を確認
                url = f"{self.api_base}/schedules/{schedule_id}/history"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    history_data = response.json()
                    history_list = history_data.get("history", [])
                    
                    if history_list:
                        latest = history_list[0]
                        logger.info(f"\n✅ タスク実行を検知!")
                        logger.info(f"  実行時刻: {latest.get('executed_at', 'N/A')}")
                        logger.info(f"  ステータス: {latest.get('status', 'N/A')}")
                        
                        # 結果の詳細
                        result_data = latest.get("result")
                        if result_data:
                            if isinstance(result_data, str):
                                try:
                                    result_data = json.loads(result_data)
                                except:
                                    pass
                            
                            if isinstance(result_data, dict):
                                logger.info(f"  取得件数: {result_data.get('fetched_count', 0)}")
                                logger.info(f"  保存件数: {result_data.get('saved_count', 0)}")
                                
                                if result_data.get('error'):
                                    logger.error(f"  エラー: {result_data['error']}")
                        
                        return True
                        
            except Exception as e:
                logger.error(f"監視エラー: {e}")
                
            # 10 秒ごとに進捗表示
            elapsed = int(time.time() - start_time)
            if elapsed - last_status_check >= 10:
                logger.info(f"  待機中... ({elapsed}秒経過)")
                last_status_check = elapsed
                
            time.sleep(check_interval)
            
        logger.warning("タイムアウト: 実行が確認できませんでした")
        return False
        
    def check_celery_beat_status(self):
        """Celery Beat の状態を確認"""
        logger.info("\nCelery Beat の状態確認中...")
        
        # スケジュール一覧を取得
        try:
            url = f"{self.api_base}/schedules"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                schedules = response.json()
                active_count = sum(1 for s in schedules if s.get('enabled', False))
                logger.info(f"  アクティブなスケジュール数: {active_count}")
                
                # 自分のスケジュールを探す
                for schedule in schedules:
                    if schedule['id'] in self.created_schedule_ids:
                        logger.info(f"  作成したスケジュール: {schedule['name']} (有効: {schedule['enabled']})")
                        
        except Exception as e:
            logger.error(f"状態確認エラー: {e}")
            
    def cleanup(self):
        """作成したスケジュールを削除"""
        logger.info("\n クリーンアップ中...")
        for schedule_id in self.created_schedule_ids:
            try:
                url = f"{self.api_base}/schedules/{schedule_id}"
                response = requests.delete(url, timeout=10)
                if response.status_code == 204:
                    logger.info(f"  ✅ スケジュール削除: {schedule_id}")
            except Exception as e:
                logger.error(f"  削除エラー: {e}")
                
    def run_test(self):
        """テストを実行"""
        logger.info("=" * 80)
        logger.info("1 分以内実行スケジュールテスト")
        logger.info("=" * 80)
        
        try:
            # 1. スケジュール作成
            schedule = self.create_schedule_for_next_minute()
            
            # 2. Celery Beat ログの確認方法を表示
            self.monitor_celery_beat()
            
            # 3. 状態確認
            self.check_celery_beat_status()
            
            # 4. 実行を監視
            success = self.monitor_execution(schedule["id"])
            
            if success:
                logger.info("\n🎉 テスト成功: タスクが正常に実行されました!")
            else:
                logger.error("\n❌ テスト失敗: タスクが実行されませんでした")
                logger.info("\n トラブルシューティング:")
                logger.info("1. Celery Beat のログを確認:")
                logger.info("   docker compose logs celery-beat --tail=100")
                logger.info("2. Celery Worker のログを確認:")
                logger.info("   docker compose logs celery-worker --tail=100")
                logger.info("3. スケジュールの同期が正しく行われているか確認")
                
        except Exception as e:
            logger.error(f"テストエラー: {e}")
        finally:
            self.cleanup()
            

def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="1 分以内に実行されるスケジュールのテスト"
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="API のベース URL"
    )
    
    args = parser.parse_args()
    
    # 環境確認
    auto_mode = os.environ.get("AUTO_MODE", "").lower() == "true"
    
    if not auto_mode:
        print("\n 前提条件:")
        print("- Docker 環境が起動していること")
        print("- Celery Beat/Worker が起動していること")
        print("- Redis Sync が有効になっていること")
        input("\nEnter キーで続行...")
        
    tester = ScheduledNowTester(base_url=args.base_url)
    tester.run_test()


if __name__ == "__main__":
    main()