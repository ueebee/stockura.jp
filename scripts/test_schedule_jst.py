#!/usr/bin/env python
"""JST タイムゾーンを考慮したスケジュールテスト"""
import os
import sys
import time
import json
import logging
import requests
import pytz
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple, List

# プロジェクトのルートディレクトリを Python パスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime) s] %(levelname) s: %(message) s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class JSTScheduleTester:
    """JST タイムゾーンを考慮したスケジュールテスト"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"
        self.created_schedule_ids: List[str] = []
        self.jst = pytz.timezone('Asia/Tokyo')
        
    def create_schedule_for_next_minute_jst(self) -> Dict:
        """次の分（JST）に実行されるスケジュールを作成"""
        url = f"{self.api_base}/schedules"
        
        # 現在時刻を取得
        now_utc = datetime.utcnow()
        now_jst = datetime.now(self.jst)
        
        # 次の分を計算（JST）
        next_minute_jst = now_jst.replace(second=0, microsecond=0) + timedelta(minutes=1)
        
        # JST の時刻をそのまま cron 式に使用
        # Celery Beat が JST で動作しているため
        cron_expression = f"{next_minute_jst.minute} {next_minute_jst.hour} * * *"
        
        logger.info(f"現在時刻 (UTC): {now_utc.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"現在時刻 (JST): {now_jst.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"実行予定 (JST): {next_minute_jst.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"cron 式 (JST 時刻): {cron_expression}")
        
        request_data = {
            "name": f"test_jst_{int(time.time())}",
            "task_name": "fetch_listed_info_task",
            "cron_expression": cron_expression,
            "description": "JST タイムゾーンテスト",
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
            wait_seconds = (next_minute_jst - datetime.now(self.jst)).total_seconds()
            logger.info(f"\n⏱️ 実行まで約 {int(wait_seconds)} 秒")
            
            return result
        except Exception as e:
            logger.error(f"スケジュール作成エラー: {e}")
            raise
            
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
        
    def check_celery_beat_logs(self):
        """Celery Beat のログ確認方法を表示"""
        logger.info("\nCelery Beat のログを確認するには:")
        logger.info("docker compose logs -f celery-beat | grep -E '(test_jst|Sending|task|due)'")
        
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
        logger.info("JST タイムゾーン対応スケジュールテスト")
        logger.info("=" * 80)
        
        try:
            # 1. スケジュール作成
            schedule = self.create_schedule_for_next_minute_jst()
            
            # 2. ログ確認方法を表示
            self.check_celery_beat_logs()
            
            # 3. 実行を監視
            success = self.monitor_execution(schedule["id"])
            
            if success:
                logger.info("\n🎉 テスト成功: タスクが正常に実行されました!")
            else:
                logger.error("\n❌ テスト失敗: タスクが実行されませんでした")
                logger.info("\n トラブルシューティング:")
                logger.info("1. Celery Beat のタイムゾーン設定を確認")
                logger.info("2. cron 式が JST 時刻になっているか確認")
                
        except Exception as e:
            logger.error(f"テストエラー: {e}")
        finally:
            self.cleanup()
            

def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="JST タイムゾーン対応スケジュールテスト"
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
        print("- Celery が JST タイムゾーンで設定されていること")
        input("\nEnter キーで続行...")
        
    tester = JSTScheduleTester(base_url=args.base_url)
    tester.run_test()


if __name__ == "__main__":
    main()