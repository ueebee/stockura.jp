#!/usr/bin/env python
"""API 経由でスケジュールを作成し、 listed_info データを取得するテストスクリプト"""
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


class ScheduledListedInfoApiTester:
    """スケジュール作成と listed_info 取得をテストするクラス"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"
        self.created_schedule_ids: List[str] = []  # クリーンアップ用
        
    def generate_cron_expression(self, minutes_from_now: int = 1) -> Tuple[str, datetime]:
        """指定分後の cron 式を生成
        
        Args:
            minutes_from_now: 現在時刻から何分後に実行するか
            
        Returns:
            (cron_expression, execution_time) のタプル
        """
        target_time = datetime.now() + timedelta(minutes=minutes_from_now)
        
        # cron 式を生成（分 時 日 月 曜日）
        cron_expression = f"{target_time.minute} {target_time.hour} * * *"
        
        logger.info(f"cron 式生成: {cron_expression} (実行予定: {target_time.strftime('%Y-%m-%d %H:%M')})")
        return cron_expression, target_time
        
    def create_schedule(
        self,
        name: str,
        cron_expression: str,
        from_date: str,
        to_date: str,
    ) -> Dict:
        """スケジュールを作成
        
        Args:
            name: スケジュール名
            cron_expression: cron 式
            from_date: データ取得開始日 (YYYY-MM-DD)
            to_date: データ取得終了日 (YYYY-MM-DD)
            
        Returns:
            作成されたスケジュールの情報
        """
        url = f"{self.api_base}/schedules"
        
        # 既存の schedules エンドポイントの形式に合わせる
        request_data = {
            "name": name,
            "task_name": "fetch_listed_info_task",
            "cron_expression": cron_expression,
            "description": f"{from_date}のデータ取得テスト",
            "enabled": True,
            "task_params": {
                "period_type": "custom",
                "from_date": from_date,
                "to_date": to_date,
                "codes": None,
                "market": None
            }
        }
        
        logger.info(f"スケジュール作成リクエスト:")
        logger.info(f"  URL: {url}")
        logger.info(f"  データ: {json.dumps(request_data, ensure_ascii=False, indent=2)}")
        
        try:
            response = requests.post(url, json=request_data, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            # クリーンアップ用に ID を保存
            self.created_schedule_ids.append(result["id"])
            
            logger.info(f"スケジュール作成成功 (ID: {result['id']})")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"スケジュール作成エラー: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"レスポンス: {e.response.text}")
            raise
            
    def get_schedule_details(self, schedule_id: str) -> Dict:
        """スケジュール詳細を取得
        
        Args:
            schedule_id: スケジュール ID
            
        Returns:
            スケジュール詳細情報
        """
        url = f"{self.api_base}/schedules/{schedule_id}"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"スケジュール詳細取得エラー: {e}")
            raise
            
    def wait_for_execution(
        self,
        execution_time: datetime,
        buffer_seconds: int = 30
    ):
        """指定時刻まで待機
        
        Args:
            execution_time: 実行予定時刻
            buffer_seconds: 追加の待機時間（秒）
        """
        now = datetime.now()
        wait_seconds = (execution_time - now).total_seconds()
        
        if wait_seconds > 0:
            total_wait = wait_seconds + buffer_seconds
            logger.info(f"実行時刻まで {total_wait:.0f} 秒待機中...")
            logger.info(f"  現在時刻: {now.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"  実行予定: {execution_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 待機中も進捗を表示
            elapsed = 0
            while elapsed < total_wait:
                remaining = total_wait - elapsed
                print(f"\r  残り {remaining:.0f} 秒...", end="", flush=True)
                time.sleep(min(10, remaining))
                elapsed += 10
            print()  # 改行
        else:
            logger.warning("実行時刻は既に過ぎています")
            
    def get_execution_history(
        self,
        schedule_id: str,
        timeout: int = 300,
        interval: int = 5
    ) -> Optional[Dict]:
        """実行履歴を監視して取得
        
        Args:
            schedule_id: スケジュール ID
            timeout: タイムアウト秒数
            interval: ポーリング間隔（秒）
            
        Returns:
            最新の実行履歴、見つからない場合は None
        """
        url = f"{self.api_base}/schedules/{schedule_id}/history"
        
        logger.info("実行履歴を監視中...")
        start_time = time.time()
        last_history_count = 0
        check_count = 0
        
        while time.time() - start_time < timeout:
            check_count += 1
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                history_data = response.json()
                
                history_list = history_data.get("history", [])
                current_count = len(history_list)
                
                if current_count > last_history_count:
                    # 新しい実行履歴を検出
                    latest = history_list[0]  # 最新の履歴は先頭
                    logger.info(f"タスク実行を検知: {latest.get('executed_at', 'N/A')}")
                    return latest
                    
                last_history_count = current_count
                
                # 進捗表示
                if check_count % 6 == 0:  # 30 秒ごと
                    elapsed = time.time() - start_time
                    logger.info(f"  監視継続中... (経過: {elapsed:.0f}秒)")
                    
            except Exception as e:
                logger.error(f"履歴取得エラー: {e}")
                
            time.sleep(interval)
            
        logger.warning(f"タイムアウト: {timeout}秒経過しました")
        return None
        
    def delete_schedule(self, schedule_id: str):
        """スケジュールを削除
        
        Args:
            schedule_id: スケジュール ID
        """
        url = f"{self.api_base}/schedules/{schedule_id}"
        
        try:
            response = requests.delete(url, timeout=10)
            response.raise_for_status()
            logger.info(f"スケジュール削除成功 (ID: {schedule_id})")
        except Exception as e:
            logger.error(f"スケジュール削除エラー: {e}")
            raise
            
    def run_full_test(self, target_date: str = "2024-08-06", wait_minutes: int = 1):
        """完全なテストシナリオを実行
        
        Args:
            target_date: データ取得対象日付 (YYYY-MM-DD)
            wait_minutes: 実行までの待機時間（分）
        """
        logger.info("=" * 80)
        logger.info("スケジュール作成テスト開始")
        logger.info(f"対象日付: {target_date}")
        logger.info(f"待機時間: {wait_minutes}分後に実行")
        logger.info("=" * 80)
        
        try:
            # 1. サーバー接続確認
            self._check_server_connection()
            
            # 2. cron 式生成
            cron_expression, execution_time = self.generate_cron_expression(minutes_from_now=wait_minutes)
            
            # 3. スケジュール作成
            schedule_name = f"test_scheduled_{target_date.replace('-', '')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            schedule = self.create_schedule(
                name=schedule_name,
                cron_expression=cron_expression,
                from_date=target_date,
                to_date=target_date
            )
            
            # 4. スケジュール詳細確認
            self._verify_schedule(schedule["id"])
            
            # 5. 実行時刻まで待機
            self.wait_for_execution(execution_time)
            
            # 6. 実行履歴を監視
            history = self.get_execution_history(schedule["id"])
            
            # 7. 結果表示
            self._display_results(history)
            
        except Exception as e:
            logger.error(f"テスト実行エラー: {e}")
            raise
        finally:
            # 8. クリーンアップ
            self._cleanup()
            
    def _check_server_connection(self):
        """サーバー接続確認"""
        logger.info("サーバー接続確認中...")
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            logger.info(f"  ✅ サーバー接続確認: OK (status: {response.status_code})")
        except Exception as e:
            logger.error(f"  ❌ サーバー接続エラー: {e}")
            logger.error("  FastAPI サーバーが起動していることを確認してください:")
            logger.error("  uvicorn app.main:app --reload")
            raise RuntimeError("FastAPI サーバーが起動していません")
            
    def _verify_schedule(self, schedule_id: str):
        """スケジュール詳細を確認"""
        logger.info("スケジュール詳細を確認中...")
        
        try:
            schedule = self.get_schedule_details(schedule_id)
            
            logger.info("スケジュール詳細:")
            logger.info(f"  ID: {schedule['id']}")
            logger.info(f"  名前: {schedule['name']}")
            logger.info(f"  cron 式: {schedule['cron_expression']}")
            logger.info(f"  有効: {schedule['enabled']}")
            logger.info(f"  説明: {schedule.get('description', 'なし')}")
            
            # kwargs の内容を確認
            kwargs = schedule.get('kwargs', {})
            if kwargs:
                logger.info(f"  パラメータ (kwargs):")
                for key, value in kwargs.items():
                    logger.info(f"    {key}: {value}")
            
        except Exception as e:
            logger.error(f"スケジュール確認エラー: {e}")
            
    def _display_results(self, history: Optional[Dict]):
        """実行結果を表示"""
        logger.info("-" * 40)
        logger.info("実行結果:")
        
        if history:
            logger.info(f"  実行時刻: {history.get('executed_at', 'N/A')}")
            logger.info(f"  ステータス: {history.get('status', 'N/A')}")
            
            # result フィールドの解析
            result_data = history.get("result")
            if result_data:
                # result が文字列の場合、 JSON としてパース
                if isinstance(result_data, str):
                    try:
                        result_data = json.loads(result_data)
                    except json.JSONDecodeError:
                        logger.warning("  結果データの解析に失敗しました")
                        
                # 結果データの表示
                if isinstance(result_data, dict):
                    logger.info("  取得結果:")
                    logger.info(f"    取得件数: {result_data.get('fetched_count', 0)}")
                    logger.info(f"    保存件数: {result_data.get('saved_count', 0)}")
                    logger.info(f"    スキップ: {result_data.get('skipped_count', 0)}")
                    
                    if "execution_time" in result_data:
                        logger.info(f"    実行時間: {result_data['execution_time']:.2f}秒")
                        
                    if "from_date" in result_data and "to_date" in result_data:
                        logger.info(f"    対象期間: {result_data['from_date']} 〜 {result_data['to_date']}")
            
            # エラー情報
            if history.get("error"):
                logger.error(f"  エラー: {history['error']}")
        else:
            logger.warning("  実行履歴が取得できませんでした")
            logger.warning("  Celery Beat が起動していることを確認してください")
            
    def _cleanup(self):
        """作成したスケジュールを削除"""
        if not self.created_schedule_ids:
            return
            
        logger.info("クリーンアップ中...")
        for schedule_id in self.created_schedule_ids:
            try:
                self.delete_schedule(schedule_id)
            except Exception as e:
                logger.warning(f"  スケジュール削除エラー (ID: {schedule_id}): {e}")


def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="API 経由でスケジュールを作成し、 listed_info データを取得するテスト"
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="FastAPI サーバーの URL (デフォルト: http://localhost:8000)"
    )
    parser.add_argument(
        "--target-date",
        default="2024-08-06",
        help="取得対象日付 (YYYY-MM-DD, デフォルト: 2024-08-06)"
    )
    parser.add_argument(
        "--wait-minutes",
        type=int,
        default=1,
        help="実行までの待機時間（分, デフォルト: 1）"
    )
    
    args = parser.parse_args()
    
    # 前提条件表示
    print("\n 前提条件:")
    print("1. FastAPI サーバーが起動していること:")
    print("   uvicorn app.main:app --reload")
    print("2. Celery ワーカーが起動していること:")
    print("   celery -A app.infrastructure.celery.app worker --loglevel=info")
    print("3. Celery Beat が起動していること:")
    print("   celery -A app.infrastructure.celery.app beat --loglevel=info")
    print("4. Redis/PostgreSQL が起動していること")
    print("-" * 40)
    
    # 自動モードかどうかをチェック
    auto_mode = os.environ.get("AUTO_MODE", "").lower() == "true"
    
    if not auto_mode:
        # 確認
        input("\n 上記の前提条件を確認してください。続行するには Enter キーを押してください...")
    else:
        print("\n 自動モードで実行中...")
    
    # テスト実行
    tester = ScheduledListedInfoApiTester(base_url=args.base_url)
    
    try:
        tester.run_full_test(
            target_date=args.target_date,
            wait_minutes=args.wait_minutes
        )
        logger.info("\n テストが正常に完了しました ✅")
    except KeyboardInterrupt:
        logger.info("\n テストを中断しました")
    except Exception as e:
        logger.error(f"\n テスト失敗: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()