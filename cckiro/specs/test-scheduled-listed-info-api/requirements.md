# 要件ファイル: API 経由でのスケジュール作成と listed_info データ取得テスト

## 1. 概要
API 経由で 1 分後に実行されるスケジュールを作成し、 8 月 6 日の listed_info データを取得するテストスクリプトを作成する。

## 2. 機能要件

### 2.1 スケジュールの作成
- cron 形式のスケジュールを API 経由で作成
- 実行時刻は現在時刻の 1 分後
- period_type は"custom"を使用
- from_date と to_date を 2024 年 8 月 6 日に設定

### 2.2 データ取得
- 8 月 6 日の listed_info データを取得
- 取得対象は全銘柄（codes パラメータは指定しない）

### 2.3 動作確認
- スケジュールの作成確認
- 1 分後の実行を待機
- タスクの実行状況をモニタリング
- 取得結果の表示

## 3. 技術要件

### 3.1 実装言語
- Python 3.x

### 3.2 使用する API
- POST `/api/v1/schedules/listed-info` - スケジュール作成
- GET `/api/v1/schedules/listed-info/{schedule_id}` - スケジュール詳細取得
- GET `/api/v1/schedules/listed-info/{schedule_id}/history` - 実行履歴取得

### 3.3 依存ライブラリ
- requests - HTTP 通信
- datetime - 日時操作

## 4. 実装要件

### 4.1 エラーハンドリング
- API エラーの適切な処理
- ネットワークエラーの処理
- タイムアウト処理

### 4.2 ログ出力
- 実行状況の詳細なログ出力
- エラー時の詳細情報表示

### 4.3 設定可能パラメータ
- base_url（デフォルト: http://localhost:8000）
- 待機タイムアウト時間
- ポーリング間隔

## 5. スクリプトファイル
- ファイル名: `scripts/test_scheduled_listed_info_api.py`
- 実行可能なスタンドアロンスクリプトとして実装

## 6. 成功基準
1. スケジュールが正常に作成される
2. 1 分後にタスクが実行される
3. 8 月 6 日の listed_info データが取得される
4. 取得結果（件数、処理時間等）が表示される