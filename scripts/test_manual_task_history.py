#!/usr/bin/env python
"""手動でタスクを実行して履歴を確認するテストスクリプト"""
import requests
import time
import json
from datetime import datetime
from uuid import uuid4

BASE_URL = "http://localhost:8000/api/v1"


def create_schedule():
    """スケジュールを作成"""
    print("スケジュールを作成中...")
    
    schedule_data = {
        "name": f"test_manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "task_name": "fetch_listed_info_task", 
        "cron_expression": "0 0 * * *",  # 実行されないダミー cron
        "description": "手動テスト用スケジュール",
        "enabled": True,
        "task_params": {
            "period_type": "yesterday",
            "from_date": None,
            "to_date": None,
            "codes": None,
            "market": None
        }
    }
    
    response = requests.post(f"{BASE_URL}/schedules", json=schedule_data)
    response.raise_for_status()
    
    schedule = response.json()
    schedule_id = schedule["id"]
    print(f"スケジュール作成成功: ID={schedule_id}")
    
    return schedule_id


def trigger_task_direct(schedule_id):
    """タスクを直接実行（Celery を使わない）"""
    print("\n タスクを直接実行中...")
    
    # /trigger/listed-info-direct エンドポイントを使用
    response = requests.post(
        f"{BASE_URL}/schedules/trigger/listed-info-direct",
        params={
            "period_type": "yesterday",
            "codes": None,
            "market": None,
            "schedule_id": schedule_id
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"タスク実行成功: {result['status']}")
        print(f"結果: {json.dumps(result['result'], ensure_ascii=False, indent=2)}")
        return result['task_id']
    else:
        print(f"タスク実行失敗: {response.status_code}")
        print(response.text)
        return None


def check_history(schedule_id):
    """履歴を確認"""
    print(f"\n 履歴を確認中（スケジュール ID: {schedule_id}）...")
    
    response = requests.get(f"{BASE_URL}/schedules/{schedule_id}/history")
    
    if response.status_code == 200:
        data = response.json()
        history = data.get("history", [])
        
        if history:
            print(f"履歴が見つかりました: {len(history)}件")
            for i, item in enumerate(history):
                print(f"\n 履歴 #{i+1}:")
                print(f"  実行時刻: {item['executed_at']}")
                print(f"  ステータス: {item['status']}")
                if item['result']:
                    print(f"  結果: {item['result']}")
                if item['error']:
                    print(f"  エラー: {item['error']}")
        else:
            print("履歴が空です")
    else:
        print(f"履歴取得エラー: {response.status_code}")
        print(response.text)


def main():
    """メイン処理"""
    print("=" * 60)
    print("手動タスク実行と履歴確認テスト")
    print("=" * 60)
    
    try:
        # 1. スケジュール作成
        schedule_id = create_schedule()
        
        # 2. タスクを手動で実行
        task_id = trigger_task_direct(schedule_id)
        
        # 3. 少し待機（データベースへの書き込みを待つ）
        print("\n3 秒待機中...")
        time.sleep(3)
        
        # 4. 履歴を確認
        check_history(schedule_id)
        
        # 5. クリーンアップ
        print("\n クリーンアップ中...")
        response = requests.delete(f"{BASE_URL}/schedules/{schedule_id}")
        if response.status_code == 204:
            print("スケジュール削除成功")
        
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()