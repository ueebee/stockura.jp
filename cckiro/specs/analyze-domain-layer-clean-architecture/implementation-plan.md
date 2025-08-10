# Domain 層クリーンアーキテクチャ改善実装計画

## 概要
設計書に基づいて、 3 つのフェーズに分けて段階的に実装を進めます。
各フェーズは独立してリリース可能であり、既存機能への影響を最小限に抑えます。

## フェーズ 1: リポジトリインターフェースの統一とファクトリーの追加（1-2 週間）

### 目的
- リポジトリインターフェースの命名規則を統一
- エンティティの外部依存を除去するための準備

### タスク一覧

#### タスク 1.1: リポジトリインターフェースのリネーム
**実装手順:**
1. `AuthRepository` → `AuthRepositoryInterface` にリネーム
2. `ListedInfoRepository` → `ListedInfoRepositoryInterface` にリネーム
3. `ScheduleRepository` を削除（`ScheduleRepositoryInterface` に統合）
4. インポート文の更新
5. テストの更新

**影響ファイル:**
- `app/domain/repositories/*.py`
- `app/infrastructure/repositories/**/*.py`
- `app/application/use_cases/*.py`
- `tests/**/*.py`

#### タスク 1.2: ScheduleRepository の統合
**実装手順:**
1. `ScheduleRepositoryInterface` のメソッドを設計書に従って統一
2. インフラストラクチャ層の実装を新しいインターフェースに合わせて修正
3. ユースケースの呼び出し箇所を更新
4. 統合テストの実施

**影響ファイル:**
- `app/domain/repositories/schedule_repository.py` (削除)
- `app/domain/repositories/schedule_repository_interface.py`
- `app/infrastructure/repositories/database/schedule_repository.py`
- `app/application/use_cases/manage_schedule.py`

#### タスク 1.3: ListedInfoFactory の実装
**実装手順:**
1. `app/application/factories/` ディレクトリを作成
2. `ListedInfoFactory` クラスを実装
3. ユニットテストを作成
4. 既存の `ListedInfo.from_dict()` の呼び出し箇所を `ListedInfoFactory` に置き換え

**新規ファイル:**
- `app/application/factories/__init__.py`
- `app/application/factories/listed_info_factory.py`
- `tests/application/factories/test_listed_info_factory.py`

#### タスク 1.4: ScheduleSerializer の実装
**実装手順:**
1. `app/application/serializers/` ディレクトリを作成
2. `ScheduleSerializer` クラスを実装
3. ユニットテストを作成
4. プレゼンテーション層での `Schedule.to_dict()` の呼び出しを置き換え

**新規ファイル:**
- `app/application/serializers/__init__.py`
- `app/application/serializers/schedule_serializer.py`
- `tests/application/serializers/test_schedule_serializer.py`

### 検証項目
- [ ] 既存の API エンドポイントが正常に動作する
- [ ] すべてのテストがパスする
- [ ] リグレッションが発生していない

## フェーズ 2: エンティティの改善とドメインサービスの実装（2-3 週間）

### 目的
- エンティティから外部依存を完全に除去
- リッチドメインモデルへの移行開始
- ドメインサービスの実装

### タスク一覧

#### タスク 2.1: ListedInfo エンティティの改修
**実装手順:**
1. `from_dict()` メソッドを削除
2. ビジネスロジックメソッドを追加
   - `is_prime_market()`
   - `is_standard_market()`
   - `is_growth_market()`
   - `belongs_to_sector_17()`
   - `belongs_to_sector_33()`
3. テストケースの追加
4. 関連するユースケースの更新

**影響ファイル:**
- `app/domain/entities/listed_info.py`
- `app/application/use_cases/fetch_listed_info.py`
- `tests/domain/entities/test_listed_info.py`

#### タスク 2.2: Schedule エンティティの改修
**実装手順:**
1. `to_dict()` メソッドを削除
2. ビジネスロジックメソッドを追加
   - `can_execute()`
   - `has_category()`
   - `has_tag()`
   - `is_auto_generated()`
3. テストケースの追加
4. プレゼンテーション層の更新（ScheduleSerializer を使用）

**影響ファイル:**
- `app/domain/entities/schedule.py`
- `app/presentation/api/v1/endpoints/schedules.py`
- `tests/domain/entities/test_schedule.py`

#### タスク 2.3: ScheduleService の実装
**実装手順:**
1. `app/domain/services/schedule_service.py` を作成
2. 以下のメソッドを実装
   - `validate_cron_expression()`
   - `find_conflicting_schedules()`
   - `generate_unique_name()`
3. ユニットテストを作成
4. ユースケースから呼び出し

**新規ファイル:**
- `app/domain/services/schedule_service.py`
- `tests/domain/services/test_schedule_service.py`

#### タスク 2.4: ListedInfoService の実装
**実装手順:**
1. `app/domain/services/listed_info_service.py` を作成
2. 以下のメソッドを実装
   - `group_by_sector_17()`
   - `group_by_market()`
   - `filter_by_scale_category()`
   - `find_changed_listings()`
3. ユニットテストを作成
4. 必要に応じてユースケースから呼び出し

**新規ファイル:**
- `app/domain/services/listed_info_service.py`
- `tests/domain/services/test_listed_info_service.py`

### 検証項目
- [ ] エンティティが外部依存を持たない
- [ ] ビジネスロジックが適切に動作する
- [ ] ドメインサービスが正しく機能する
- [ ] パフォーマンスの劣化がない

## フェーズ 3: ドメインイベントの実装（3-4 週間）

### 目的
- イベント駆動アーキテクチャの基盤を構築
- 重要なビジネスイベントをドメインイベントとして定義

### タスク一覧

#### タスク 3.1: ドメインイベント基盤の実装
**実装手順:**
1. `app/domain/events/` ディレクトリ構造を作成
2. `DomainEvent` 基底クラスを実装
3. イベントディスパッチャーの基本実装
4. ユニットテストを作成

**新規ファイル:**
- `app/domain/events/__init__.py`
- `app/domain/events/base.py`
- `app/domain/events/dispatcher.py`
- `tests/domain/events/test_base.py`

#### タスク 3.2: スケジュール関連イベントの実装
**実装手順:**
1. `schedule_events.py` を作成
2. 各イベントクラスを実装
   - `ScheduleCreatedEvent`
   - `ScheduleUpdatedEvent`
   - `ScheduleEnabledEvent`
   - `ScheduleDisabledEvent`
   - `ScheduleDeletedEvent`
3. テストケースの作成

**新規ファイル:**
- `app/domain/events/schedule_events.py`
- `tests/domain/events/test_schedule_events.py`

#### タスク 3.3: 上場銘柄情報関連イベントの実装
**実装手順:**
1. `listed_info_events.py` を作成
2. 各イベントクラスを実装
   - `ListedInfosFetchedEvent`
   - `ListedInfosStoredEvent`
   - `NewListingsDetectedEvent`
   - `DelistingsDetectedEvent`
   - `MarketChangeDetectedEvent`
3. テストケースの作成

**新規ファイル:**
- `app/domain/events/listed_info_events.py`
- `tests/domain/events/test_listed_info_events.py`

#### タスク 3.4: イベント発行の統合
**実装手順:**
1. エンティティにイベント発行機能を追加（オプション）
2. ユースケースからイベントを発行
3. イベントハンドラーの基本実装
4. 統合テストの実施

**影響ファイル:**
- `app/application/use_cases/*.py`
- `app/infrastructure/events/` (新規)

### 検証項目
- [ ] イベントが正しく発行される
- [ ] イベントハンドラーが適切に動作する
- [ ] 既存機能に影響がない
- [ ] イベントの永続化が可能（オプション）

## リスク管理

### リスク 1: 後方互換性の破壊
**対策:**
- 各フェーズで API レスポンスの形式が変わらないことを確認
- 段階的な移行でビッグバンリリースを回避
- 十分なテストカバレッジを維持

### リスク 2: パフォーマンスの劣化
**対策:**
- 各フェーズでパフォーマンステストを実施
- 必要に応じて最適化を実施
- キャッシュ戦略の見直し

### リスク 3: チームメンバーの学習コスト
**対策:**
- 各フェーズ完了時にドキュメントを更新
- コードレビューでの知識共有
- ペアプログラミングの活用

## 成功基準

### フェーズ 1 完了時
- すべてのリポジトリインターフェースが統一された命名規則に従っている
- ファクトリーとシリアライザーが正しく機能している
- 既存のテストがすべてパスしている

### フェーズ 2 完了時
- エンティティが外部依存を持たない
- ビジネスロジックがエンティティまたはドメインサービスに適切に配置されている
- コードカバレッジが向上している

### フェーズ 3 完了時
- ドメインイベントが正しく発行・処理されている
- イベント駆動の基盤が確立されている
- 将来の拡張が容易になっている

## タイムライン

```
Week 1-2: フェーズ 1（リポジトリインターフェースの統一）
Week 3-5: フェーズ 2（エンティティの改善）
Week 6-8: フェーズ 3（ドメインイベントの実装）
Week 9:   最終テストとドキュメント整備
```

## 実装の開始

フェーズ 1 から順番に実装を進めます。各タスクは独立性が高いため、
複数の開発者で並行して作業することも可能です。

実装中は以下を心がけます：
- テスト駆動開発（TDD）の実践
- こまめなコミットとプルリクエスト
- コードレビューの徹底
- ドキュメントの同時更新