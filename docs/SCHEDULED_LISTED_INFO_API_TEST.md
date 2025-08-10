# スケジュール listed_info API テストガイド

## 概要

API 経由でスケジュールを作成し、 listed_info データを取得するテストスクリプトの使用方法について説明します。

## 実装されたスクリプト

### テストスクリプト: `scripts/test_scheduled_listed_info_api.py`

このスクリプトは以下の処理を実行します：

1. 現在時刻から 1 分後に実行される cron スケジュールを生成
2. API 経由でスケジュールを作成（8 月 6 日のデータ取得用）
3. スケジュールの実行を待機
4. 実行結果を監視して表示
5. テスト完了後にスケジュールを削除（クリーンアップ）

## 前提条件

以下のサービスが起動している必要があります：

1. **FastAPI サーバー**
   ```bash
   uvicorn app.main:app --reload
   ```

2. **Celery ワーカー**
   ```bash
   celery -A app.infrastructure.celery.app worker --loglevel=info
   ```

3. **Celery Beat**
   ```bash
   celery -A app.infrastructure.celery.app beat --loglevel=info
   ```

4. **Redis/PostgreSQL**
   - Docker Compose で起動済みであることを確認

## 使用方法

### Makefile を使った実行（推奨）

```bash
# インタラクティブモード（確認プロンプトあり）
make test-scheduled-api

# 自動モード（確認プロンプトなし）
make test-scheduled-api-auto
```

### 直接実行

```bash
# 基本的な実行
python scripts/test_scheduled_listed_info_api.py

# 自動モード
AUTO_MODE=true python scripts/test_scheduled_listed_info_api.py
```

### オプション指定

```bash
# API サーバーの URL を指定
python scripts/test_scheduled_listed_info_api.py --base-url http://localhost:8000

# 取得対象日付を指定
python scripts/test_scheduled_listed_info_api.py --target-date 2024-08-06

# 実行までの待機時間を指定（デフォルト: 1 分）
python scripts/test_scheduled_listed_info_api.py --wait-minutes 2
```

## 実行例

```bash
$ python scripts/test_scheduled_listed_info_api.py

前提条件:
1. FastAPI サーバーが起動していること:
   uvicorn app.main:app --reload
2. Celery ワーカーが起動していること:
   celery -A app.infrastructure.celery.app worker --loglevel=info
3. Celery Beat が起動していること:
   celery -A app.infrastructure.celery.app beat --loglevel=info
4. Redis/PostgreSQL が起動していること
----------------------------------------

上記の前提条件を確認してください。続行するには Enter キーを押してください...

[2024-XX-XX HH:MM:SS] INFO: ================================================================================
[2024-XX-XX HH:MM:SS] INFO: スケジュール作成テスト開始
[2024-XX-XX HH:MM:SS] INFO: 対象日付: 2024-08-06
[2024-XX-XX HH:MM:SS] INFO: 待機時間: 1 分後に実行
[2024-XX-XX HH:MM:SS] INFO: ================================================================================
[2024-XX-XX HH:MM:SS] INFO: サーバー接続確認中...
[2024-XX-XX HH:MM:SS] INFO:   ✅ サーバー接続確認: OK (status: 200)
[2024-XX-XX HH:MM:SS] INFO: cron 式生成: 30 14 * * * (実行予定: 2024-XX-XX 14:30)
[2024-XX-XX HH:MM:SS] INFO: スケジュール作成リクエスト:
[2024-XX-XX HH:MM:SS] INFO:   URL: http://localhost:8000/api/v1/schedules/listed-info
[2024-XX-XX HH:MM:SS] INFO:   データ: {
  "name": "test_scheduled_20240806_20241125_143000",
  "cron_expression": "30 14 * * *",
  "period_type": "custom",
  "description": "2024-08-06 のデータ取得テスト",
  "enabled": true,
  "codes": null,
  "market": null,
  "from_date": "2024-08-06",
  "to_date": "2024-08-06"
}
[2024-XX-XX HH:MM:SS] INFO: スケジュール作成成功 (ID: xxxx-xxxx-xxxx-xxxx)
[2024-XX-XX HH:MM:SS] INFO: スケジュール詳細を確認中...
[2024-XX-XX HH:MM:SS] INFO: スケジュール詳細:
[2024-XX-XX HH:MM:SS] INFO:   ID: xxxx-xxxx-xxxx-xxxx
[2024-XX-XX HH:MM:SS] INFO:   名前: test_scheduled_20240806_20241125_143000
[2024-XX-XX HH:MM:SS] INFO:   cron 式: 30 14 * * *
[2024-XX-XX HH:MM:SS] INFO:   有効: True
[2024-XX-XX HH:MM:SS] INFO:   説明: 2024-08-06 のデータ取得テスト
[2024-XX-XX HH:MM:SS] INFO:   パラメータ (kwargs):
[2024-XX-XX HH:MM:SS] INFO:     period_type: custom
[2024-XX-XX HH:MM:SS] INFO:     codes: []
[2024-XX-XX HH:MM:SS] INFO:     market: None
[2024-XX-XX HH:MM:SS] INFO:     from_date: 2024-08-06
[2024-XX-XX HH:MM:SS] INFO:     to_date: 2024-08-06
[2024-XX-XX HH:MM:SS] INFO: 実行時刻まで 90 秒待機中...
[2024-XX-XX HH:MM:SS] INFO:   現在時刻: 2024-XX-XX 14:28:30
[2024-XX-XX HH:MM:SS] INFO:   実行予定: 2024-XX-XX 14:30:00
  残り 90 秒...
  残り 80 秒...
  ...
[2024-XX-XX HH:MM:SS] INFO: 実行履歴を監視中...
[2024-XX-XX HH:MM:SS] INFO: タスク実行を検知: 2024-XX-XX 14:30:01
[2024-XX-XX HH:MM:SS] INFO: ----------------------------------------
[2024-XX-XX HH:MM:SS] INFO: 実行結果:
[2024-XX-XX HH:MM:SS] INFO:   実行時刻: 2024-XX-XX 14:30:01
[2024-XX-XX HH:MM:SS] INFO:   ステータス: SUCCESS
[2024-XX-XX HH:MM:SS] INFO:   取得結果:
[2024-XX-XX HH:MM:SS] INFO:     取得件数: 4000
[2024-XX-XX HH:MM:SS] INFO:     保存件数: 4000
[2024-XX-XX HH:MM:SS] INFO:     スキップ: 0
[2024-XX-XX HH:MM:SS] INFO:     実行時間: 15.23 秒
[2024-XX-XX HH:MM:SS] INFO:     対象期間: 2024-08-06 〜 2024-08-06
[2024-XX-XX HH:MM:SS] INFO: クリーンアップ中...
[2024-XX-XX HH:MM:SS] INFO: スケジュール削除成功 (ID: xxxx-xxxx-xxxx-xxxx)

テストが正常に完了しました ✅
```

## カスタム期間タイプの実装

### API の変更点

1. **DTO の更新** (`app/application/dtos/listed_info_schedule_dto.py`)
   - `CreateListedInfoScheduleDTO` に `from_date` と `to_date` フィールドを追加
   - `period_type` が "custom" の場合の検証ロジックを追加

2. **ユースケースの更新** (`app/application/use_cases/manage_listed_info_schedule.py`)
   - `create_schedule` メソッドに `from_date` と `to_date` パラメータを追加
   - "custom" period_type の場合、 kwargs に日付情報を含める処理を追加

3. **API エンドポイントの更新** (`app/presentation/api/v1/endpoints/listed_info_schedules.py`)
   - リクエストから `from_date` と `to_date` を受け取りユースケースに渡す

### CLI の変更点

`scripts/manage_listed_info_schedule.py` に以下を追加：
- `--from-date` と `--to-date` オプション
- "custom" period_type 使用時の検証ロジック

## トラブルシューティング

### サーバー接続エラー
```
[ERROR] サーバー接続エラー: ...
FastAPI サーバーが起動していません
```
→ FastAPI サーバーが起動していることを確認してください

### スケジュールが実行されない
```
[WARNING] タイムアウト: 300 秒経過しました
```
→ Celery Beat が起動していることを確認してください

### データ取得エラー
- J-Quants API の認証情報が正しく設定されているか確認
- ネットワーク接続を確認

## 関連ファイル

- **テストスクリプト**: `scripts/test_scheduled_listed_info_api.py`
- **spec-driven 開発ドキュメント**: `cckiro/specs/test-scheduled-listed-info-api/`
  - `requirements.md`: 要件定義
  - `design.md`: 設計仕様
  - `implementation-plan.md`: 実装計画