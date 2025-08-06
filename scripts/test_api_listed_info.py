#!/usr/bin/env python
"""API 経由で listed_info タスクを手動実行するテストスクリプト"""
import sys
import time
import json
from pathlib import Path
from typing import Optional, List
import requests
from datetime import datetime

# プロジェクトのルートディレクトリを Python パスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))


class ListedInfoApiTester:
    """API 経由で listed_info タスクを実行・確認するクラス"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"
        
    def trigger_task(
        self,
        period_type: str = "yesterday",
        codes: Optional[List[str]] = None,
        market: Optional[str] = None,
    ) -> dict:
        """タスクをトリガーする
        
        Args:
            period_type: 期間タイプ (yesterday, 7days, 30days, custom)
            codes: 銘柄コードのリスト（オプション）
            market: 市場コード（オプション）
            
        Returns:
            タスク実行情報
        """
        url = f"{self.api_base}/schedules/trigger/listed-info"
        
        params = {
            "period_type": period_type,
        }
        if codes:
            params["codes"] = codes
        if market:
            params["market"] = market
            
        print(f"\n📤 タスクをトリガーしています...")
        print(f"   URL: {url}")
        print(f"   パラメータ: {json.dumps(params, ensure_ascii=False, indent=2)}")
        
        try:
            response = requests.post(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"\n❌ エラー: {e}")
            if hasattr(e.response, 'text'):
                print(f"   詳細: {e.response.text}")
            raise
            
    def check_task_status(self, task_id: str) -> dict:
        """タスクのステータスを確認する
        
        Args:
            task_id: Celery タスク ID
            
        Returns:
            タスクステータス情報
        """
        url = f"{self.api_base}/schedules/tasks/{task_id}/status"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"\n❌ ステータス確認エラー: {e}")
            raise
            
    def wait_for_task(self, task_id: str, timeout: int = 300, interval: int = 5) -> dict:
        """タスクの完了を待つ
        
        Args:
            task_id: Celery タスク ID
            timeout: タイムアウト秒数
            interval: ポーリング間隔（秒）
            
        Returns:
            最終的なタスクステータス
        """
        print(f"\n⏳ タスク完了を待機中... (最大{timeout}秒)")
        
        start_time = time.time()
        last_status = None
        
        while time.time() - start_time < timeout:
            status = self.check_task_status(task_id)
            
            if status["status"] != last_status:
                print(f"   ステータス: {status['status']} ({datetime.now().strftime('%H:%M:%S')})")
                last_status = status["status"]
                
            if status["ready"]:
                return status
                
            time.sleep(interval)
            
        print(f"\n⚠️  タイムアウト: {timeout}秒経過しました")
        return self.check_task_status(task_id)
        
    def run_full_test(
        self,
        period_type: str = "yesterday",
        codes: Optional[List[str]] = None,
        market: Optional[str] = None,
    ):
        """完全なテストフローを実行"""
        print("=" * 80)
        print("Listed Info API テスト")
        print("=" * 80)
        
        # 1. サーバー接続確認
        print("\n1️⃣  サーバー接続確認...")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            print(f"   ✅ サーバーは稼働中です")
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            print(f"   ❌ サーバーに接続できません")
            print(f"   FastAPI サーバーが起動していることを確認してください:")
            print(f"   uvicorn app.main:app --reload")
            print("
   ⚠️  サーバーが起動していないため、このテストをスキップします")
            return
            
        # 2. タスクをトリガー
        print("\n2️⃣  タスクをトリガー...")
        try:
            trigger_result = self.trigger_task(period_type, codes, market)
            task_id = trigger_result["task_id"]
            
            print(f"\n   ✅ タスクがキューに追加されました")
            print(f"   タスク ID: {task_id}")
            print(f"   送信時刻: {trigger_result['submitted_at']}")
        except Exception as e:
            print(f"\n   ❌ タスクのトリガーに失敗しました: {e}")
            return
            
        # 3. タスクの完了を待つ
        print("\n3️⃣  タスク実行を監視...")
        final_status = self.wait_for_task(task_id)
        
        # 4. 結果を表示
        print("\n4️⃣  実行結果:")
        print("-" * 40)
        
        if final_status["ready"]:
            if final_status["status"] == "SUCCESS":
                print("   ✅ タスクが正常に完了しました")
                
                if "result" in final_status:
                    result = final_status["result"]
                    print(f"\n   詳細結果:")
                    print(json.dumps(result, ensure_ascii=False, indent=4))
                    
                    # 統計情報を表示
                    if isinstance(result, dict):
                        if "fetched_count" in result:
                            print(f"\n   📊 統計:")
                            print(f"      取得件数: {result.get('fetched_count', 0)}")
                            print(f"      保存件数: {result.get('saved_count', 0)}")
                            print(f"      スキップ: {result.get('skipped_count', 0)}")
                            
                        if "execution_time" in result:
                            print(f"      実行時間: {result['execution_time']:.2f}秒")
            else:
                print(f"   ❌ タスクが失敗しました")
                print(f"   ステータス: {final_status['status']}")
                if "error" in final_status:
                    print(f"   エラー: {final_status['error']}")
        else:
            print(f"   ⏳ タスクはまだ実行中です")
            print(f"   ステータス: {final_status['status']}")
            
        print("\n" + "=" * 80)
        

def main():
    """メイン関数"""
    print("Listed Info API テストツール")
    print("-" * 40)
    
    # テスターインスタンスを作成
    tester = ListedInfoApiTester()
    
    # メニュー表示
    print("\n テストオプション:")
    print("1. 昨日のデータを取得（全銘柄）")
    print("2. 特定銘柄の昨日のデータを取得")
    print("3. 特定市場の昨日のデータを取得")
    print("4. カスタムパラメータで実行")
    print("5. 簡易実行（昨日のデータ、結果待機なし）")
    
    choice = input("\n 選択 (1-5): ").strip()
    
    if choice == "1":
        # 昨日のデータを全取得
        tester.run_full_test(period_type="yesterday")
        
    elif choice == "2":
        # 特定銘柄
        codes_input = input("銘柄コード（カンマ区切り）: ").strip()
        codes = [c.strip() for c in codes_input.split(",") if c.strip()]
        
        if codes:
            tester.run_full_test(period_type="yesterday", codes=codes)
        else:
            print("銘柄コードが入力されていません")
            
    elif choice == "3":
        # 特定市場
        market = input("市場コード (例: 0111=プライム): ").strip()
        
        if market:
            tester.run_full_test(period_type="yesterday", market=market)
        else:
            print("市場コードが入力されていません")
            
    elif choice == "4":
        # カスタム
        period_type = input("期間タイプ (yesterday/7days/30days): ").strip() or "yesterday"
        codes_input = input("銘柄コード（カンマ区切り、空欄で全銘柄）: ").strip()
        codes = [c.strip() for c in codes_input.split(",") if c.strip()] if codes_input else None
        market = input("市場コード（空欄で全市場）: ").strip() or None
        
        tester.run_full_test(period_type=period_type, codes=codes, market=market)
        
    elif choice == "5":
        # 簡易実行
        print("\n 簡易実行モード（結果を待機しません）")
        try:
            result = tester.trigger_task(period_type="yesterday")
            print(f"\n✅ タスクが送信されました")
            print(f"タスク ID: {result['task_id']}")
            print(f"\n ステータス確認 URL:")
            print(f"curl http://localhost:8000/api/v1/schedules/tasks/{result['task_id']}/status")
        except Exception as e:
            print(f"❌ エラー: {e}")
            
    else:
        print("無効な選択です")
        

if __name__ == "__main__":
    print("\n 前提条件:")
    print("1. FastAPI サーバーが起動していること:")
    print("   uvicorn app.main:app --reload")
    print("2. Celery ワーカーが起動していること:")
    print("   celery -A app.infrastructure.celery.app worker --loglevel=info")
    print("3. Redis/PostgreSQL が起動していること")
    print("-" * 40)
    
    main()