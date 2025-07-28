# テストカバレッジ向上 要件定義書

## 1. 目的
- 現在のテストカバレッジ率を分析し、目標値（80% 以上）を達成する
- 重要なビジネスロジックと API エンドポイントのテストカバレッジを優先的に向上させる

## 2. 現状分析要件
- 現在のカバレッジ率の測定と分析
- カバレッジが不足している主要モジュールの特定
- 未テストのクリティカルなコードパスの洗い出し

### 2.1 現在のカバレッジ状況
- **全体カバレッジ率**: 41.60% (目標: 80%)
- **テスト数**: 115 テスト (114 passed, 1 skipped)
- **カバレッジが 0% の主要モジュール**:
  - `app/application/dtos/stock_dto.py` (97 行)
  - `app/application/interfaces/external/jquants_client.py` (38 行)
  - `app/application/interfaces/external/yfinance_client.py` (44 行)
  - `app/application/interfaces/repositories/stock_repository.py` (35 行)
  - `app/application/use_cases/analyze_stock.py` (92 行)
  - `app/application/use_cases/fetch_stock_price.py` (57 行)
  - `app/infrastructure/jquants/stock_repository_impl.py` (94 行)
  - `app/infrastructure/database/repositories/stock_repository_impl.py` (82 行)
  - `app/domain/services/price_calculator.py` (92 行)

### 2.2 高カバレッジモジュール (参考)
- `app/domain/entities/stock.py`: 100%
- `app/application/use_cases/auth_use_case.py`: 97.37%
- `app/application/use_cases/stock_use_case.py`: 96.61%
- `app/infrastructure/jquants/auth_repository_impl.py`: 95.29%

## 3. 機能要件
### 3.1 カバレッジ分析
- pytest-cov を使用した詳細なカバレッジレポートの生成
- モジュール別、クラス別のカバレッジ率の可視化
- 未カバーの行番号とコードの特定

### 3.2 テスト追加対象の優先順位付け
- ビジネスクリティカルな機能の特定
- 複雑度の高いロジックの優先
- API エンドポイントのテスト網羅

### 3.3 テストの品質基準
- 単体テストの独立性確保
- モックの適切な使用
- エッジケースとエラーハンドリングのテスト
- パフォーマンステストの考慮（必要に応じて）

## 4. 非機能要件
### 4.1 テストの実行速度
- 既存のテスト実行時間を大幅に増加させない
- 並列実行可能なテスト設計

### 4.2 保守性
- テストコードの可読性とメンテナンス性
- テストユーティリティとフィクスチャの共通化
- ドキュメント化されたテストケース

### 4.3 CI/CD 統合
- GitHub Actions 等でのカバレッジチェック
- プルリクエスト時の自動カバレッジレポート

## 5. 成功基準
- 全体のテストカバレッジ率が 80% 以上
- コアモジュールのカバレッジ率が 90% 以上
- 新規追加コードのカバレッジ率が 95% 以上
- すべての API エンドポイントがテストされている

## 6. 制約事項
- 既存のテストを壊さない
- プロダクションコードの変更は最小限に留める
- テストのためだけのコード変更は避ける

## 7. 優先度別実装計画
### 7.1 最優先（Phase 1）
1. **Stock 関連のユースケース** (約 180 行のカバレッジ向上)
   - `analyze_stock.py`: 株式分析のコアロジック
   - `fetch_stock_price.py`: 価格取得のコアロジック

2. **JQuants Stock Repository 実装** (94 行)
   - `stock_repository_impl.py`: データ取得の中核実装

### 7.2 高優先度（Phase 2）
1. **DTO とインターフェース** (約 214 行)
   - `stock_dto.py`: データ変換ロジック
   - `jquants_client.py`, `yfinance_client.py`: 外部 API 連携
   - `stock_repository.py`: リポジトリインターフェース

2. **価格計算サービス** (92 行)
   - `price_calculator.py`: 価格計算ロジック

### 7.3 中優先度（Phase 3）
1. **データベース関連** (約 115 行)
   - `stock_repository_impl.py` (DB 版)
   - `connection.py`: DB 接続管理

2. **その他のドメインロジック** (約 219 行)
   - Value Objects
   - 例外クラス
   - 定数定義

## 8. テスト戦略
### 8.1 単体テスト
- 各ユースケースの正常系・異常系テスト
- モックを活用した外部依存の分離
- エラーハンドリングの網羅的テスト

### 8.2 統合テスト
- リポジトリ実装の実際の API 連携テスト（テスト環境）
- データベース接続を含むテスト

### 8.3 E2E テスト
- 主要なユーザーシナリオのテスト
- API エンドポイント経由の完全なフローテスト