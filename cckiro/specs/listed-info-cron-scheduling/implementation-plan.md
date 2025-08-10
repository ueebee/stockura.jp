# 実装計画ファイル: listed_info タスクの cron 形式スケジューリング機能

## 1. 実装フェーズと優先順位

### フェーズ 1: 基盤整備（優先度: 高）
1. ドメイン層の実装
   - cron 式バリデーター
   - カスタム例外クラス
   - スケジュールプリセット

2. Use Case 層の実装
   - `ManageListedInfoScheduleUseCase`の作成

### フェーズ 2: API 実装（優先度: 高）
1. DTO の作成
2. API エンドポイントの実装
3. API テストの作成

### フェーズ 3: CLI 実装（優先度: 中）
1. CLI コマンドの実装
2. CLI テストの作成

### フェーズ 4: 統合テスト（優先度: 高）
1. E2E テストの作成
2. ドキュメントの作成

## 2. 詳細実装手順

### 2.1 ドメイン層

#### 2.1.1 cron 式バリデーター
**ファイル**: `app/domain/validators/cron_validator.py`
```python
# 実装内容:
# - validate_cron_expression(): cron 式の妥当性検証
# - get_next_run_time(): 次回実行時刻の計算
# - get_cron_description(): cron 式の説明文生成
```

#### 2.1.2 カスタム例外
**ファイル**: `app/domain/exceptions/schedule_exceptions.py`
```python
# 実装内容:
# - ScheduleException: 基底例外クラス
# - InvalidCronExpressionException: 無効な cron 式
# - ScheduleConflictException: スケジュール名重複
# - ScheduleNotFoundException: スケジュール未発見
```

#### 2.1.3 スケジュールプリセット
**ファイル**: `app/domain/helpers/schedule_presets.py`
```python
# 実装内容:
# - SCHEDULE_PRESETS 定数の定義
# - get_preset_description(): プリセットの説明取得
```

### 2.2 Use Case 層

#### 2.2.1 ManageListedInfoScheduleUseCase
**ファイル**: `app/application/use_cases/manage_listed_info_schedule.py`
```python
# 実装内容:
# - create_schedule(): スケジュール作成
# - update_schedule(): スケジュール更新
# - delete_schedule(): スケジュール削除
# - get_schedule(): スケジュール取得
# - list_schedules(): スケジュール一覧
# - toggle_schedule(): 有効/無効切り替え
```

### 2.3 DTO 層

#### 2.3.1 スケジュール DTO
**ファイル**: `app/application/dtos/listed_info_schedule_dto.py`
```python
# 実装内容:
# - CreateListedInfoScheduleDTO
# - UpdateListedInfoScheduleDTO
# - ListedInfoScheduleDTO
# - ListedInfoScheduleListDTO
```

### 2.4 API 層

#### 2.4.1 API エンドポイント
**ファイル**: `app/presentation/api/v1/endpoints/listed_info_schedules.py`
```python
# 実装内容:
# - POST /api/v1/schedules/listed-info
# - GET /api/v1/schedules/listed-info
# - GET /api/v1/schedules/listed-info/{schedule_id}
# - PUT /api/v1/schedules/listed-info/{schedule_id}
# - DELETE /api/v1/schedules/listed-info/{schedule_id}
# - POST /api/v1/schedules/listed-info/{schedule_id}/toggle
# - GET /api/v1/schedules/listed-info/{schedule_id}/history
```

### 2.5 CLI 層

#### 2.5.1 CLI コマンド
**ファイル**: `scripts/manage_listed_info_schedule.py`
```python
# 実装内容:
# - create: スケジュール作成
# - list: スケジュール一覧
# - show: スケジュール詳細
# - update: スケジュール更新
# - delete: スケジュール削除
# - enable/disable: 有効/無効切り替え
# - validate-cron: cron 式検証
```

## 3. テスト計画

### 3.1 単体テスト
```
tests/unit/domain/validators/test_cron_validator.py
tests/unit/domain/exceptions/test_schedule_exceptions.py
tests/unit/domain/helpers/test_schedule_presets.py
tests/unit/application/use_cases/test_manage_listed_info_schedule.py
tests/unit/application/dtos/test_listed_info_schedule_dto.py
```

### 3.2 統合テスト
```
tests/integration/api/test_listed_info_schedules.py
tests/integration/cli/test_manage_listed_info_schedule.py
```

### 3.3 E2E テスト
```
tests/e2e/test_listed_info_cron_scheduling.py
```

## 4. 依存関係

### 4.1 新規パッケージ
```
croniter==2.0.1  # cron 式の解析・検証
```

### 4.2 既存コンポーネントの利用
- `CeleryBeatSchedule`モデル
- `ScheduleRepository`（既存）
- `fetch_listed_info_task`（変更なし）

## 5. 実装順序とタイムライン

### Week 1
1. ドメイン層の実装（validators, exceptions, helpers）
2. Use Case 層の実装
3. DTO 層の実装
4. 単体テストの作成

### Week 2
1. API エンドポイントの実装
2. CLI コマンドの実装
3. 統合テストの作成
4. E2E テストの作成

### Week 3
1. ドキュメントの作成
2. コードレビューと修正
3. デプロイ準備

## 6. リスクと対策

### 6.1 技術的リスク
- **リスク**: cron 式の複雑性による入力ミス
- **対策**: プリセットの提供、バリデーション強化、説明文の自動生成

### 6.2 運用リスク
- **リスク**: スケジュール重複による負荷
- **対策**: 実行ポリシーの活用、同時実行制限

## 7. 完了条件

1. 全ての API エンドポイントが正常に動作する
2. CLI コマンドが全機能利用可能
3. テストカバレッジ 80% 以上
4. ドキュメントが完成
5. コードレビューが完了

## 8. 実装時の注意事項

1. **既存実装への影響を最小限に**
   - `fetch_listed_info_task`は変更しない
   - 既存のスケジュール実行に影響を与えない

2. **エラーハンドリングの徹底**
   - ユーザーフレンドリーなエラーメッセージ
   - 詳細なログ出力

3. **パフォーマンス考慮**
   - スケジュール一覧取得時のページネーション
   - 実行履歴の保持期間設定

4. **セキュリティ**
   - API の認証必須
   - 入力値の厳密な検証