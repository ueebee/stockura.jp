# 設計: Docker 環境での Redis Sync 設定問題の解決

## 概要

Docker 環境でスケジュールタスクの実行履歴が確認できない問題を解決するための設計。根本原因は、 Redis Sync 機能は実装済みであり、環境変数も.env ファイルに設定されているが、 Docker 環境特有の問題により正常に動作していない可能性がある。

## 問題分析

### 現状の構成
1. **環境変数の状況**
   - .env ファイルには CELERY_BEAT_REDIS_SYNC 関連の設定が存在
   - docker-compose.yml は.env ファイルを読み込んでいる（.env.docker ではない）
   - 各コンテナには環境変数が渡されているはず

2. **Redis Sync 実装**
   - DatabaseSchedulerAsyncPG クラスに実装済み
   - 初期化時に Redis Sync が有効な場合、サブスクライバースレッドを起動
   - ログ出力も実装されている

### 考えられる問題
1. **Docker 環境でのログレベル**
   - docker-compose.dev.yml で LOG_LEVEL=DEBUG が設定されているが、 INFO レベルのログが出力されていない可能性

2. **Redis コンテナ間通信**
   - Docker 内部ネットワークでの Redis 接続に問題がある可能性
   - パブリッシュ側とサブスクライブ側で異なる Redis 接続を使用している可能性

3. **環境変数の優先順位**
   - docker-compose.yml の environment セクションで一部の環境変数を上書きしている
   - env_file と environment の優先順位により、設定が期待通りに反映されていない可能性

## 設計方針

### 1. 診断機能の追加
- Docker 環境での設定確認スクリプトを作成
- 実行時の環境変数と Redis 接続状態を確認

### 2. ログ出力の改善
- Celery Beat の起動時に Redis Sync 設定の状態を明示的にログ出力
- Redis 接続の成功/失敗をログに記録

### 3. Docker Compose 設定の修正
- 必要な環境変数を明示的に各コンテナに渡す
- ログレベルを適切に設定

### 4. テストツールの改善
- monitor_redis_events_docker.sh を拡張して診断機能を追加
- Docker 環境専用のテストスクリプトを作成

## 実装設計

### 1. 診断スクリプト（scripts/diagnose_redis_sync_docker.py）
```python
# Docker 環境での Redis Sync 設定を診断
- 環境変数の確認
- Redis 接続テスト
- Celery Beat 設定の確認
- パブリッシュ/サブスクライブのテスト
```

### 2. DatabaseSchedulerAsyncPG の改善
- 起動時のログ出力を詳細化
- Redis 接続エラーの詳細なログ出力
- 環境変数の読み込み状態をログ出力

### 3. Docker Compose 設定の更新
```yaml
# celery-beat サービスに明示的に環境変数を追加
environment:
  - CELERY_BEAT_REDIS_SYNC_ENABLED=${CELERY_BEAT_REDIS_SYNC_ENABLED}
  - CELERY_BEAT_MIN_SYNC_INTERVAL=${CELERY_BEAT_MIN_SYNC_INTERVAL}
  - CELERY_BEAT_REDIS_CHANNEL=${CELERY_BEAT_REDIS_CHANNEL}
```

### 4. 統合テストの改善
- Docker 環境での実行を前提としたテストスクリプト
- 各コンポーネントの動作確認を段階的に実施

## 実装の優先順位

1. **診断スクリプトの作成**（最優先）
   - 現状の問題を正確に把握するため

2. **ログ出力の改善**
   - 問題の発生箇所を特定しやすくする

3. **Docker Compose 設定の修正**
   - 環境変数が確実に渡されるようにする

4. **テストスクリプトの改善**
   - 問題が解決したことを確認

## リスクと対策

### リスク
- 既存の動作に影響を与える可能性
- Docker 環境とローカル環境での動作の差異

### 対策
- 変更は最小限に留める
- 既存の実装を変更せず、設定とログ出力の改善に注力
- 段階的に変更を適用し、各段階で動作確認を実施