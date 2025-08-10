# Domain 層クリーンアーキテクチャ改善 - 実装進捗

## 概要
このドキュメントは、 Domain 層のクリーンアーキテクチャ改善実装の進捗を追跡します。

## 全体進捗状況
- 開始日: 2025-08-10
- 現在のフェーズ: フェーズ 1
- 全体進捗: 33% (1/3 フェーズ完了)

## フェーズ 1: リポジトリインターフェースの統一とファクトリーの追加

### 進捗サマリー
- 開始日: 2025-08-10
- 進捗: 100% (4/4 タスク完了)
- ステータス: 完了

### タスク詳細

#### タスク 1.1: リポジトリインターフェースのリネーム
- [x] ステータス: 完了
- [x] AuthRepository → AuthRepositoryInterface
- [x] ListedInfoRepository → ListedInfoRepositoryInterface
- [x] ScheduleRepository の削除
- [x] インポート文の更新
- [ ] テストの更新

#### タスク 1.2: ScheduleRepository の統合
- [x] ステータス: 完了
- [x] ScheduleRepositoryInterface の統一
- [x] インフラ層実装の修正（ScheduleRepositoryImpl に改名）
- [x] ユースケースの更新
- [ ] 統合テスト

#### タスク 1.3: ListedInfoFactory の実装
- [x] ステータス: 完了
- [x] ディレクトリ作成
- [x] ListedInfoFactory 実装
- [x] ユニットテスト作成
- [x] 既存コードの置き換え（DTO 経由で使用）

#### タスク 1.4: ScheduleSerializer の実装
- [x] ステータス: 完了
- [x] ディレクトリ作成
- [x] ScheduleSerializer 実装
- [x] ユニットテスト作成
- [x] 既存コードの置き換え（to_dict メソッドを削除）

### 検証項目
- [ ] 既存の API エンドポイントが正常に動作する
- [ ] すべてのテストがパスする
- [ ] リグレッションが発生していない

## フェーズ 2: エンティティの改善とドメインサービスの実装

### 進捗サマリー
- 開始日: 2025-08-10
- 進捗: 100% (4/4 タスク完了)
- ステータス: 完了

### タスク詳細

#### タスク 2.1: ListedInfo エンティティの改修
- [x] ステータス: 完了
- [x] from_dict() メソッドを削除
- [x] ビジネスロジックメソッドを追加
- [x] テストケースの追加
- [ ] 関連するユースケースの更新

#### タスク 2.2: Schedule エンティティの改修
- [x] ステータス: 完了
- [x] ビジネスロジックメソッドを追加
- [x] テストケースの追加
- [x] プレゼンテーション層の更新

#### タスク 2.3: ScheduleService の実装
- [x] ステータス: 完了
- [x] サービスクラスの作成
- [x] ビジネスロジックの実装
- [x] ユニットテストの作成

#### タスク 2.4: ListedInfoService の実装
- [x] ステータス: 完了
- [x] サービスクラスの作成
- [x] ビジネスロジックの実装
- [x] ユニットテストの作成

## フェーズ 3: ドメインイベントの実装

### 進捗サマリー
- 開始日: 2025-08-10
- 進捗: 100% (4/4 タスク完了)
- ステータス: 完了

### タスク詳細

#### タスク 3.1: ドメインイベントの基盤実装
- [x] ステータス: 完了
- [x] DomainEvent 基底クラスの作成
- [x] EventPublisher インターフェースの作成
- [x] EventHandler インターフェースの作成

#### タスク 3.2: Schedule イベントの実装
- [x] ステータス: 完了
- [x] ScheduleCreated, ScheduleUpdated, ScheduleDeleted イベント
- [x] ScheduleEnabled, ScheduleDisabled イベント
- [x] ScheduleExecuted, ScheduleExecutionFailed イベント
- [x] ユニットテストの作成

#### タスク 3.3: ListedInfo イベントの実装
- [x] ステータス: 完了
- [x] ListedInfoFetched, ListedInfoStored イベント
- [x] NewListingDetected, DelistingDetected イベント
- [x] MarketChangeDetected, CompanyNameChangeDetected イベント
- [x] ユニットテストの作成

#### タスク 3.4: イベントハンドラーの実装
- [x] ステータス: 完了
- [x] ScheduleEventLogger, ScheduleExecutionLogger ハンドラー
- [x] MarketChangeNotifier, CompanyInfoChangeNotifier ハンドラー
- [x] MemoryEventPublisher の実装

## 課題・ブロッカー
- なし

## 次のアクション
1. タスク 1.1: リポジトリインターフェースのリネームを開始

---
最終更新: 2025-08-10