# 上場銘柄一覧（listed_info）データ取得・格納機能 実装計画書

## 1. 実装概要

J-Quants API の listed_info エンドポイントからデータを取得し、 PostgreSQL に格納する機能を実装する。

## 2. 実装フェーズ

### Phase 1: インフラストラクチャ層の実装（2 日）

#### Day 1: データベース層
1. **データベースモデルの作成**
   - `app/infrastructure/database/models/listed_info_model.py`
   - SQLAlchemy モデルの定義
   - インデックスの設定

2. **マイグレーションファイルの作成**
   - Alembic を使用したマイグレーション
   - listed_info テーブルの作成
   - 複合主キー（date, code）の設定

3. **リポジトリ実装**
   - `app/infrastructure/database/repositories/listed_info_repository_impl.py`
   - UPSERT 処理の実装
   - バルクインサートの最適化

#### Day 2: API クライアント層
1. **J-Quants クライアント拡張**
   - `app/infrastructure/jquants/listed_info_client.py`
   - listed_info エンドポイントの実装
   - 既存の認証機能を活用

2. **リトライ機構の実装**
   - `app/infrastructure/jquants/retry_handler.py`
   - 指数バックオフ付きリトライ
   - エラーハンドリング

### Phase 2: ドメイン層の実装（1 日）

1. **エンティティの作成**
   - `app/domain/entities/listed_info.py`
   - 不変データクラスとして実装
   - バリデーションロジック

2. **リポジトリインターフェース**
   - `app/domain/repositories/listed_info_repository.py`
   - 抽象基底クラスの定義

3. **カスタム例外**
   - `app/domain/exceptions/listed_info_exceptions.py`
   - エラー階層の定義

### Phase 3: アプリケーション層の実装（1 日）

1. **DTO の作成**
   - `app/application/dtos/listed_info_dto.py`
   - API レスポンスからの変換
   - エンティティへの変換

2. **ユースケースの実装**
   - `app/application/use_cases/fetch_listed_info.py`
   - ビジネスロジックの実装
   - エラーハンドリング

### Phase 4: プレゼンテーション層の実装（0.5 日）

1. **CLI コマンドの実装**
   - `app/presentation/cli/commands/fetch_listed_info_command.py`
   - Click を使用したコマンド定義
   - 進捗表示とロギング

### Phase 5: テストの実装（1.5 日）

1. **ユニットテスト**
   - エンティティのテスト
   - DTO 変換のテスト
   - ユースケースのテスト

2. **統合テスト**
   - API クライアントのテスト（VCR 使用）
   - リポジトリのテスト
   - E2E テスト

## 3. 実装の詳細

### 3.1 データベーススキーマ

```sql
CREATE TABLE listed_info (
    date DATE NOT NULL,
    code VARCHAR(4) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    company_name_english VARCHAR(255),
    sector_17_code VARCHAR(10),
    sector_17_code_name VARCHAR(255),
    sector_33_code VARCHAR(10),
    sector_33_code_name VARCHAR(255),
    scale_category VARCHAR(50),
    market_code VARCHAR(10),
    market_code_name VARCHAR(50),
    margin_code VARCHAR(10),
    margin_code_name VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (date, code)
);
```

### 3.2 API レスポンス形式

```json
{
  "info": [
    {
      "Date": "2023-01-04",
      "Code": "1301",
      "CompanyName": "極洋",
      "CompanyNameEnglish": "KYOKUYO CO.,LTD.",
      "Sector17Code": "0050",
      "Sector17CodeName": "水産・農林業",
      "Sector33Code": "0050",
      "Sector33CodeName": "水産・農林業",
      "ScaleCategory": "TOPIX Small 2",
      "MarketCode": "0111",
      "MarketCodeName": "プライム"
    }
  ]
}
```

### 3.3 実装順序の詳細

1. **準備作業**
   - 既存コードベースの確認
   - 依存関係の確認
   - テスト環境の準備

2. **実装作業**
   - ボトムアップアプローチ（インフラ → ドメイン → アプリケーション）
   - 各レイヤーでのテスト実装
   - CI での自動テスト実行

3. **検証作業**
   - ローカル環境での動作確認
   - パフォーマンステスト
   - セキュリティレビュー

## 4. 技術的考慮事項

### 4.1 パフォーマンス最適化
- バッチサイズ: 1000 件単位での処理
- PostgreSQL の COPY コマンドの検討
- インデックスの適切な設定

### 4.2 エラーハンドリング
- API レート制限への対応
- ネットワークエラーのリトライ
- データ不整合の検出と修正

### 4.3 監視とログ
- 処理時間の計測
- エラー率の監視
- 詳細なログ出力

## 5. リスクと対策

### 5.1 技術的リスク
- **リスク**: 大量データ処理によるメモリ不足
  - **対策**: ストリーミング処理の実装

- **リスク**: API レート制限
  - **対策**: 適切な待機時間の実装

### 5.2 スケジュールリスク
- **リスク**: 予期せぬ技術的課題
  - **対策**: バッファ時間の確保

## 6. 成功基準

1. **機能要件の達成**
   - 全銘柄データの取得成功
   - データベースへの正常な格納
   - エラー時の適切なハンドリング

2. **非機能要件の達成**
   - 処理時間: 5 分以内（全銘柄）
   - エラー率: 1% 未満
   - テストカバレッジ: 80% 以上

## 7. 実装チェックリスト

### Phase 1: インフラストラクチャ層
- [ ] データベースモデルの作成
- [ ] マイグレーションの実行
- [ ] リポジトリ実装（UPSERT 対応）
- [ ] API クライアントの拡張
- [ ] リトライ機構の実装
- [ ] インフラ層のユニットテスト

### Phase 2: ドメイン層
- [ ] ListedInfo エンティティの作成
- [ ] リポジトリインターフェースの定義
- [ ] カスタム例外の定義
- [ ] ドメイン層のユニットテスト

### Phase 3: アプリケーション層
- [ ] ListedInfoDTO の作成
- [ ] FetchListedInfoUseCase の実装
- [ ] アプリケーション層のユニットテスト

### Phase 4: プレゼンテーション層
- [ ] CLI コマンドの実装
- [ ] コマンドのヘルプとドキュメント
- [ ] 統合テスト

### Phase 5: テストと文書化
- [ ] 全レイヤーのテスト実装
- [ ] E2E テストの実装
- [ ] 使用方法のドキュメント作成
- [ ] パフォーマンステストの実施

## 8. 実装開始前の確認事項

1. **環境準備**
   - PostgreSQL の接続確認
   - J-Quants API の認証情報確認
   - テスト用データベースの準備

2. **依存関係**
   - 既存の認証機能の動作確認
   - データベースマイグレーションツールの確認
   - テストフレームワークの設定確認

3. **コーディング規約**
   - 型ヒントの使用
   - エラーハンドリングのパターン
   - ログ出力の形式

## 9. まとめ

本実装計画に従って、段階的に機能を実装していく。各フェーズでテストを実施し、品質を確保しながら進める。全体で約 6 日間の実装期間を見込む。