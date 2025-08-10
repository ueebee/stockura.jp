# 設計ファイル: API 経由でのスケジュール作成と listed_info データ取得テスト

## 1. システム構成

### 1.1 全体アーキテクチャ
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Test Script    │────▶│  FastAPI        │────▶│ Celery Beat     │
│                 │     │  Server         │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                       │
         │                       ▼                       ▼
         │              ┌─────────────────┐     ┌─────────────────┐
         └─────────────▶│   Database      │     │ Celery Worker   │
                        │ (PostgreSQL)    │     │                 │
                        └─────────────────┘     └─────────────────┘
```

### 1.2 処理フロー
1. スクリプト起動
2. 現在時刻から 1 分後の cron 式を生成
3. API 経由でスケジュール作成
4. 作成されたスケジュールの確認
5. 1 分間待機
6. 実行履歴の監視
7. 結果の表示

## 2. クラス設計

### 2.1 ScheduledListedInfoApiTester
```python
class ScheduledListedInfoApiTester:
    """スケジュール作成と listed_info 取得をテストするクラス"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"
        
    def generate_cron_expression(self, minutes_from_now: int = 1) -> tuple[str, datetime]:
        """指定分後の cron 式を生成"""
        
    def create_schedule(
        self,
        name: str,
        cron_expression: str,
        from_date: str,
        to_date: str,
    ) -> dict:
        """スケジュールを作成"""
        
    def get_schedule_details(self, schedule_id: str) -> dict:
        """スケジュール詳細を取得"""
        
    def wait_for_execution(
        self,
        execution_time: datetime,
        buffer_seconds: int = 30
    ):
        """指定時刻まで待機"""
        
    def get_execution_history(
        self,
        schedule_id: str,
        timeout: int = 300,
        interval: int = 5
    ) -> dict:
        """実行履歴を監視して取得"""
        
    def delete_schedule(self, schedule_id: str):
        """テスト後のクリーンアップ"""
        
    def run_full_test(self, target_date: str = "2024-08-06"):
        """完全なテストシナリオを実行"""
```

## 3. API 仕様

### 3.1 スケジュール作成 API
```json
POST /api/v1/schedules/listed-info
{
    "name": "test_scheduled_20240806_YYYYMMDD_HHMMSS",
    "cron_expression": "M H * * *",
    "period_type": "custom",
    "description": "8 月 6 日のデータ取得テスト",
    "enabled": true,
    "codes": null,
    "market": null
}
```

### 3.2 スケジュール作成後の kwargs 構造
```json
{
    "period_type": "custom",
    "from_date": "2024-08-06",
    "to_date": "2024-08-06",
    "codes": [],
    "market": null
}
```

## 4. エラーハンドリング設計

### 4.1 エラー種別
1. **接続エラー**: FastAPI サーバーへの接続失敗
2. **API エラー**: 400 番台、 500 番台の HTTP エラー
3. **タイムアウト**: スケジュール実行の待機タイムアウト
4. **データ不整合**: 期待するレスポンス形式と異なる

### 4.2 リトライ戦略
- API 呼び出し: 3 回まで、指数バックオフ
- 実行履歴確認: タイムアウトまで定期的にポーリング

## 5. ログ設計

### 5.1 ログレベル
- INFO: 正常な処理フロー
- WARNING: リトライ発生、待機時間延長
- ERROR: 処理失敗、例外発生

### 5.2 ログ出力例
```
[2024-XX-XX HH:MM:SS] INFO: スケジュール作成開始
[2024-XX-XX HH:MM:SS] INFO: cron 式生成: M H * * * (実行予定: YYYY-MM-DD HH:MM)
[2024-XX-XX HH:MM:SS] INFO: スケジュール作成成功 (ID: xxxx-xxxx-xxxx)
[2024-XX-XX HH:MM:SS] INFO: 実行時刻まで待機中...
[2024-XX-XX HH:MM:SS] INFO: タスク実行を検知
[2024-XX-XX HH:MM:SS] INFO: 取得結果: X 件のデータを取得
```

## 6. テストシナリオ

### 6.1 正常系
1. スケジュール作成
2. 1 分後に実行
3. 8 月 6 日のデータ取得成功
4. 結果表示
5. スケジュール削除

### 6.2 異常系
1. サーバー未起動時の処理
2. 無効な cron 式での作成
3. 実行タイムアウト
4. データ取得失敗

## 7. 実装上の注意点

### 7.1 時刻処理
- タイムゾーンの考慮（JST/UTC）
- 1 分後の時刻計算の精度
- Celery Beat のスケジュール更新タイミング

### 7.2 クリーンアップ
- テスト終了後のスケジュール削除
- 異常終了時のリソース解放

### 7.3 並行実行対策
- スケジュール名の一意性確保（タイムスタンプ付与）
- 同時実行時の競合回避