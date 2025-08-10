# 実装計画: API 経由でのスケジュール作成と listed_info データ取得テスト

## 1. 実装タスクの概要

### 1.1 主要タスク
1. テストスクリプトの基本構造作成
2. API クライアント機能の実装
3. cron 式生成ロジックの実装
4. スケジュール作成・監視機能の実装
5. エラーハンドリングとログ出力の実装
6. 統合テストシナリオの実装

### 1.2 実装順序
1. ファイル作成とクラス定義
2. 初期化処理とユーティリティメソッド
3. API 通信メソッド
4. メインテストロジック
5. エラーハンドリングとクリーンアップ

## 2. 詳細実装計画

### 2.1 Phase 1: 基本構造の作成（10 分）
```python
# scripts/test_scheduled_listed_info_api.py

#!/usr/bin/env python
"""API 経由でスケジュールを作成し、 listed_info データを取得するテストスクリプト"""
import sys
import time
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
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
```

### 2.2 Phase 2: クラス定義と初期化（15 分）

#### ScheduledListedInfoApiTester クラス
```python
class ScheduledListedInfoApiTester:
    """スケジュール作成と listed_info 取得をテストするクラス"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"
        self.created_schedule_ids = []  # クリーンアップ用
```

### 2.3 Phase 3: cron 式生成機能（20 分）

#### generate_cron_expression メソッド
```python
def generate_cron_expression(self, minutes_from_now: int = 1) -> Tuple[str, datetime]:
    """指定分後の cron 式を生成
    
    Returns:
        (cron_expression, execution_time) のタプル
    """
    target_time = datetime.now() + timedelta(minutes=minutes_from_now)
    
    # cron 式を生成（分 時 日 月 曜日）
    cron_expression = f"{target_time.minute} {target_time.hour} * * *"
    
    logger.info(f"cron 式生成: {cron_expression} (実行予定: {target_time.strftime('%Y-%m-%d %H:%M')})")
    return cron_expression, target_time
```

### 2.4 Phase 4: スケジュール作成機能（25 分）

#### create_schedule メソッド
```python
def create_schedule(
    self,
    name: str,
    cron_expression: str,
    from_date: str,
    to_date: str,
) -> Dict:
    """スケジュールを作成"""
    url = f"{self.api_base}/schedules/listed-info"
    
    request_data = {
        "name": name,
        "cron_expression": cron_expression,
        "period_type": "custom",
        "description": f"{from_date}のデータ取得テスト",
        "enabled": True,
        "codes": None,
        "market": None
    }
    
    # from_date と to_date は kwargs に含まれる
    # API は period_type="custom" の場合、内部で kwargs を設定
    
    try:
        response = requests.post(url, json=request_data)
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
```

### 2.5 Phase 5: 実行監視機能（30 分）

#### wait_for_execution メソッド
```python
def wait_for_execution(
    self,
    execution_time: datetime,
    buffer_seconds: int = 30
):
    """指定時刻まで待機"""
    now = datetime.now()
    wait_seconds = (execution_time - now).total_seconds()
    
    if wait_seconds > 0:
        logger.info(f"実行時刻まで {wait_seconds:.0f} 秒待機中...")
        time.sleep(wait_seconds + buffer_seconds)
    else:
        logger.warning("実行時刻は既に過ぎています")
```

#### get_execution_history メソッド
```python
def get_execution_history(
    self,
    schedule_id: str,
    timeout: int = 300,
    interval: int = 5
) -> Optional[Dict]:
    """実行履歴を監視して取得"""
    url = f"{self.api_base}/schedules/listed-info/{schedule_id}/history"
    
    start_time = time.time()
    last_history_count = 0
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url)
            response.raise_for_status()
            history_data = response.json()
            
            if history_data["history"] and len(history_data["history"]) > last_history_count:
                # 新しい実行履歴を検出
                latest = history_data["history"][0]
                logger.info(f"タスク実行を検知: {latest.get('executed_at', 'N/A')}")
                return latest
                
            last_history_count = len(history_data.get("history", []))
            
        except Exception as e:
            logger.error(f"履歴取得エラー: {e}")
            
        time.sleep(interval)
        
    logger.warning(f"タイムアウト: {timeout}秒経過しました")
    return None
```

### 2.6 Phase 6: メインテストロジック（35 分）

#### run_full_test メソッド
```python
def run_full_test(self, target_date: str = "2024-08-06"):
    """完全なテストシナリオを実行"""
    logger.info("=" * 80)
    logger.info("スケジュール作成テスト開始")
    logger.info(f"対象日付: {target_date}")
    logger.info("=" * 80)
    
    try:
        # 1. サーバー接続確認
        self._check_server_connection()
        
        # 2. cron 式生成
        cron_expression, execution_time = self.generate_cron_expression(minutes_from_now=1)
        
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
```

### 2.7 Phase 7: ヘルパーメソッド（20 分）

#### サーバー接続確認
```python
def _check_server_connection(self):
    """サーバー接続確認"""
    try:
        response = requests.get(f"{self.base_url}/", timeout=5)
        logger.info(f"サーバー接続確認: OK (status: {response.status_code})")
    except Exception as e:
        logger.error(f"サーバー接続エラー: {e}")
        raise RuntimeError("FastAPI サーバーが起動していません")
```

#### スケジュール確認
```python
def _verify_schedule(self, schedule_id: str):
    """スケジュール詳細を確認"""
    url = f"{self.api_base}/schedules/listed-info/{schedule_id}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        schedule = response.json()
        
        logger.info("スケジュール詳細:")
        logger.info(f"  名前: {schedule['name']}")
        logger.info(f"  cron 式: {schedule['cron_expression']}")
        logger.info(f"  有効: {schedule['enabled']}")
        logger.info(f"  kwargs: {json.dumps(schedule.get('kwargs', {}), ensure_ascii=False)}")
        
    except Exception as e:
        logger.error(f"スケジュール確認エラー: {e}")
```

#### 結果表示
```python
def _display_results(self, history: Optional[Dict]):
    """実行結果を表示"""
    logger.info("-" * 40)
    logger.info("実行結果:")
    
    if history:
        logger.info(f"  実行時刻: {history.get('executed_at', 'N/A')}")
        logger.info(f"  ステータス: {history.get('status', 'N/A')}")
        
        if history.get("result"):
            result = history["result"]
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except:
                    pass
                    
            if isinstance(result, dict):
                logger.info(f"  取得件数: {result.get('fetched_count', 0)}")
                logger.info(f"  保存件数: {result.get('saved_count', 0)}")
                logger.info(f"  実行時間: {result.get('execution_time', 0):.2f}秒")
        
        if history.get("error"):
            logger.error(f"  エラー: {history['error']}")
    else:
        logger.warning("  実行履歴が取得できませんでした")
```

### 2.8 Phase 8: クリーンアップとメイン関数（15 分）

#### クリーンアップ
```python
def _cleanup(self):
    """作成したスケジュールを削除"""
    for schedule_id in self.created_schedule_ids:
        try:
            self.delete_schedule(schedule_id)
        except Exception as e:
            logger.warning(f"スケジュール削除エラー (ID: {schedule_id}): {e}")

def delete_schedule(self, schedule_id: str):
    """スケジュールを削除"""
    url = f"{self.api_base}/schedules/listed-info/{schedule_id}"
    
    try:
        response = requests.delete(url)
        response.raise_for_status()
        logger.info(f"スケジュール削除成功 (ID: {schedule_id})")
    except Exception as e:
        logger.error(f"スケジュール削除エラー: {e}")
        raise
```

#### メイン関数
```python
def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="API 経由でスケジュールを作成し、 listed_info データを取得するテスト"
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="FastAPI サーバーの URL"
    )
    parser.add_argument(
        "--target-date",
        default="2024-08-06",
        help="取得対象日付 (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--wait-minutes",
        type=int,
        default=1,
        help="実行までの待機時間（分）"
    )
    
    args = parser.parse_args()
    
    # 前提条件表示
    print("\n 前提条件:")
    print("1. FastAPI サーバーが起動していること")
    print("2. Celery ワーカーが起動していること")
    print("3. Celery Beat が起動していること")
    print("4. Redis/PostgreSQL が起動していること")
    print("-" * 40)
    
    # テスト実行
    tester = ScheduledListedInfoApiTester(base_url=args.base_url)
    
    try:
        # wait_minutes を考慮した cron 式生成に修正が必要
        tester.run_full_test(target_date=args.target_date)
    except KeyboardInterrupt:
        logger.info("\n テストを中断しました")
    except Exception as e:
        logger.error(f"テスト失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## 3. 実装時の注意点

### 3.1 エラーハンドリング
- API 通信エラーは詳細なログ出力
- タイムアウト設定の適切な調整
- 異常終了時のクリーンアップ確保

### 3.2 ログ出力
- 実行状況を追跡しやすいログ構成
- エラー時は詳細情報を含める
- タイムスタンプ付きで出力

### 3.3 テスト容易性
- コマンドライン引数で柔軟な設定
- デバッグしやすい構造
- 再実行可能な設計

## 4. テストとデバッグ

### 4.1 単体テスト項目
1. cron 式生成の正確性
2. API エンドポイントへの接続
3. エラーレスポンスの処理
4. タイムアウト処理

### 4.2 統合テスト項目
1. エンドツーエンドの動作確認
2. 実際のデータ取得確認
3. クリーンアップの動作確認

## 5. 実装完了基準

1. ✅ スクリプトが正常に起動する
2. ✅ 1 分後の cron 式が正確に生成される
3. ✅ API 経由でスケジュールが作成される
4. ✅ スケジュールが指定時刻に実行される
5. ✅ 8 月 6 日のデータが取得される
6. ✅ 結果が適切に表示される
7. ✅ クリーンアップが正常に動作する
8. ✅ エラー時の適切な処理とログ出力

## 6. 推定作業時間

- 総作業時間: 約 2 時間
  - Phase 1-2: 25 分（基本構造）
  - Phase 3-4: 45 分（コア機能）
  - Phase 5-6: 65 分（監視とテスト）
  - Phase 7-8: 35 分（補助機能）
  - デバッグ・調整: 10 分