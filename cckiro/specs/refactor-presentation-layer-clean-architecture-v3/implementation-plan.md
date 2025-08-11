# Presentation 層クリーンアーキテクチャ改善実装計画（第 3 回）

## Phase 1: 基本的な Mapper 基盤の実装

### 1.1 BaseMapper の実装
- [ ] `app/presentation/api/v1/mappers/__init__.py` を作成
- [ ] `app/presentation/api/v1/mappers/base.py` を作成
  - BaseMapper の抽象基底クラスを定義
  - ジェネリック型を使用してスキーマと DTO の型を定義

### 1.2 AutoMapper の実装
- [ ] `app/presentation/api/v1/mappers/auto_mapper.py` を作成
  - 自動フィールドマッピング機能を実装
  - 型チェック機能を実装
  - Pydantic モデルと dataclass の相互変換に対応

### 1.3 単体テストの作成
- [ ] `tests/unit/presentation/mappers/test_auto_mapper.py` を作成
  - 自動マッピング機能のテスト
  - 型チェック機能のテスト
  - エッジケースのテスト

## Phase 2: Schedule 関連の Mapper 実装

### 2.1 ScheduleMapper の実装
- [ ] `app/presentation/api/v1/mappers/schedule_mapper.py` を作成
  - ScheduleCreate → ScheduleCreateDto の変換
  - ScheduleDto → ScheduleResponse の変換
  - TaskParams → TaskParamsDto の変換

### 2.2 依存性注入の設定
- [ ] `app/presentation/dependencies/mappers.py` を作成
  - get_schedule_mapper 関数を実装

### 2.3 エンドポイントの移行
- [ ] `app/presentation/api/v1/endpoints/schedules.py` を更新
  - create_schedule エンドポイントを Mapper を使用するように修正
  - list_schedules エンドポイントを Mapper を使用するように修正
  - get_schedule エンドポイントを Mapper を使用するように修正
  - update_schedule エンドポイントを Mapper を使用するように修正

### 2.4 統合テストの実施
- [ ] 既存の Schedule 関連テストがすべて通ることを確認
- [ ] 必要に応じてテストを修正

## Phase 3: その他のエンドポイントの移行

### 3.1 Auth 関連の Mapper
- [ ] `app/presentation/api/v1/mappers/auth_mapper.py` を作成
- [ ] auth エンドポイントの移行

### 3.2 ListedInfo 関連の Mapper
- [ ] `app/presentation/api/v1/mappers/listed_info_mapper.py` を作成
- [ ] listed_info_schedules エンドポイントの移行

### 3.3 全体テストの実施
- [ ] すべての既存テストが通ることを確認
- [ ] E2E テストの実施

## 実装時の注意事項

1. **動作確認の徹底**
   - 各 Phase の完了時に必ずテストを実行
   - API の動作確認を行う

2. **段階的な実装**
   - 一度に全てを変更せず、小さな単位で実装
   - 各ステップでコミット

3. **既存コードとの互換性**
   - API インターフェースは変更しない
   - 既存の DTO は変更しない

4. **エラーハンドリング**
   - マッピングエラーの適切な処理
   - わかりやすいエラーメッセージ

## 完了基準

- [ ] すべてのエンドポイントが Mapper を使用している
- [ ] データ変換ロジックがエンドポイントから分離されている
- [ ] 既存のテストがすべて通る
- [ ] 新規作成した Mapper の単体テストがある
- [ ] ドキュメントの更新（必要に応じて）