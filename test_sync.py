#!/usr/bin/env python3
import requests
from datetime import date, timedelta

# 6月4日のデータを取得
target_date = date(2025, 6, 4)

# APIエンドポイント
url = "http://localhost:8000/api/v1/daily-quotes/sync/manual"

# パラメータ
params = {
    "sync_type": "incremental",
    "data_source_id": 1,
    "target_date": target_date.isoformat()
}

# リクエスト送信
print(f"Sending sync request for {target_date.isoformat()}...")
response = requests.post(url, params=params)

if response.status_code == 200:
    data = response.json()
    print(f"Task ID: {data.get('task_id')}")
    print(f"Status: {data.get('status')}")
    print(f"Message: {data.get('message')}")
    
    # タスクステータスを確認
    if data.get('task_id'):
        import time
        task_id = data['task_id']
        for i in range(10):
            time.sleep(2)
            status_response = requests.get(f"http://localhost:8000/api/v1/daily-quotes/sync/task/{task_id}")
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"\nCheck {i+1}: State={status_data.get('state')}, Status={status_data.get('status')}")
                if status_data.get('state') in ['SUCCESS', 'FAILURE']:
                    print(f"Final result: {status_data}")
                    break
else:
    print(f"Error: {response.status_code}")
    print(response.text)