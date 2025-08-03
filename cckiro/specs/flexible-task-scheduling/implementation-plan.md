# タスクスケジューリング改善実装計画

## 実装概要

設計に基づいて、段階的に機能を実装します。 Phase 1 のコア機能を最優先で実装し、その後 Phase 2 、 Phase 3 と進めます。

## Phase 1: コア機能の実装（必須）

### 1.1 データベースマイグレーション

**作業内容:**
1. Alembic マイグレーションファイルの作成
2. UNIQUE 制約の削除
3. 新しいカラムの追加
4. インデックスの追加

**ファイル:**
- `alembic/versions/xxx_flexible_task_scheduling.py`

**実装手順:**
```bash
# マイグレーションファイルの生成
python scripts/db_migrate.py revision -m "flexible_task_scheduling"
```

### 1.2 ドメインエンティティの修正

**作業内容:**
1. Schedule エンティティに新しいフィールドを追加
2. to_dict メソッドの更新

**ファイル:**
- `app/domain/entities/schedule.py`

### 1.3 データベースモデルの修正

**作業内容:**
1. CeleryBeatSchedule モデルに新しいカラムを追加
2. UNIQUE 制約の削除

**ファイル:**
- `app/infrastructure/database/models/schedule.py`

### 1.4 リポジトリの修正

**作業内容:**
1. 新しいフィールドのマッピング追加
2. 検索機能の強化（カテゴリー、タグでのフィルタリング）

**ファイル:**
- `app/infrastructure/repositories/schedule_repository.py`
- `app/domain/repositories/schedule_repository_interface.py`

### 1.5 DTO の修正

**作業内容:**
1. ScheduleDTO に新しいフィールドを追加
2. CreateScheduleDTO 、 UpdateScheduleDTO の更新

**ファイル:**
- `app/application/dto/schedule_dto.py`

### 1.6 ユースケースの修正

**作業内容:**
1. CreateScheduleUseCase の修正（名前の重複チェックを削除）
2. ListSchedulesUseCase の修正（フィルタリング機能追加）

**ファイル:**
- `app/application/use_cases/manage_schedule.py`

### 1.7 API スキーマの修正

**作業内容:**
1. ScheduleCreate スキーマの更新
2. ScheduleResponse スキーマの更新
3. ScheduleFilter スキーマの追加

**ファイル:**
- `app/presentation/api/v1/schemas/schedule.py`

### 1.8 API エンドポイントの修正

**作業内容:**
1. 作成エンドポイントの更新
2. 一覧取得エンドポイントのフィルタリング機能追加

**ファイル:**
- `app/presentation/api/v1/endpoints/schedules.py`

### 1.9 テストの更新

**作業内容:**
1. 既存テストの修正（UNIQUE 制約関連）
2. 新機能のテスト追加

**ファイル:**
- `tests/unit/domain/entities/test_schedule.py`
- `tests/unit/infrastructure/repositories/test_schedule_repository.py`
- `tests/unit/application/use_cases/test_manage_schedule_use_case.py`
- `tests/unit/presentation/api/v1/endpoints/test_schedules.py`

## Phase 2: 拡張機能の実装（推奨）

### 2.1 TaskDefinition の実装

**作業内容:**
1. TaskDefinition エンティティの作成
2. task_definitions テーブルの作成
3. TaskDefinitionRepository の実装
4. タスク定義管理 API の追加

**新規ファイル:**
- `app/domain/entities/task_definition.py`
- `app/infrastructure/database/models/task_definition.py`
- `app/infrastructure/repositories/task_definition_repository.py`
- `app/application/use_cases/manage_task_definition.py`

### 2.2 スケジュール名自動生成

**作業内容:**
1. ScheduleNameGenerator クラスの実装
2. CreateScheduleUseCase への統合

**新規ファイル:**
- `app/domain/services/schedule_name_generator.py`

### 2.3 パラメータバリデーション

**作業内容:**
1. JSON Schema バリデータの実装
2. CreateScheduleUseCase への統合

**新規ファイル:**
- `app/domain/validators/task_parameter_validator.py`

## Phase 3: 高度な機能の実装（オプション）

### 3.1 実行ポリシー機能

**作業内容:**
1. TaskExecutionController の実装
2. Redis 連携の設定
3. タスクデコレータの修正

**新規ファイル:**
- `app/infrastructure/celery/controllers/task_execution_controller.py`

### 3.2 タスク実装の修正

**作業内容:**
1. 既存タスクに実行ポリシー対応を追加
2. schedule_name パラメータの追加

**ファイル:**
- `app/infrastructure/celery/tasks/listed_info_task_asyncpg.py`

### 3.3 タスク実行ログの強化

**作業内容:**
1. TaskExecutionLog に schedule_name フィールドを追加
2. ログ記録の更新

**ファイル:**
- `app/domain/entities/task_log.py`
- `app/infrastructure/database/models/task_log.py`

## 実装スケジュール

### Week 1: Phase 1 実装
- Day 1-2: データベースマイグレーション、エンティティ修正
- Day 3-4: リポジトリ、ユースケース修正
- Day 5: API 修正、テスト更新

### Week 2: Phase 2 実装
- Day 1-2: TaskDefinition 実装
- Day 3: スケジュール名自動生成
- Day 4-5: パラメータバリデーション、統合テスト

### Week 3: Phase 3 実装（オプション）
- Day 1-2: 実行ポリシー機能
- Day 3-4: タスク実装の修正
- Day 5: 全体テスト、ドキュメント更新

## リスクと対策

### 1. データベースマイグレーションのリスク

**リスク:** 既存データへの影響
**対策:** 
- バックアップの取得
- ステージング環境での十分なテスト
- ロールバック手順の準備

### 2. パフォーマンスへの影響

**リスク:** スケジュール数増加によるパフォーマンス低下
**対策:**
- 適切なインデックスの設定
- ページネーションの実装
- キャッシュの活用

### 3. 既存タスクへの影響

**リスク:** 実行中のタスクへの影響
**対策:**
- 後方互換性の維持
- 段階的なロールアウト
- 十分なテスト

## 成功の測定基準

1. **機能面**
   - 同一タスクの複数スケジュール登録が可能
   - 既存のスケジュールが正常に動作
   - API レスポンスタイムが現状と同等

2. **運用面**
   - スケジュール管理の効率化
   - エラー率の低下
   - 運用チームからのポジティブなフィードバック

## 実装時の注意事項

1. **コーディング規約**
   - Black でのフォーマット
   - 型ヒントの使用
   - 適切なログ出力

2. **テスト**
   - 単体テストのカバレッジ 80% 以上
   - 統合テストの実施
   - E2E テストの更新

3. **ドキュメント**
   - API ドキュメントの更新
   - 運用手順書の更新
   - CLAUDE.md への追記