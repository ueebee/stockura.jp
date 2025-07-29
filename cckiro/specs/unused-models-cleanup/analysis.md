# 不要なモデル・関連部分の洗い出し仕様書

## 概要
本仕様書は、プロジェクト内の不要なモデルおよび関連するコードを特定し、削除対象を明確にすることを目的とします。

## 現状分析

### 1. データベースモデル

#### 1.1 StockModel (`app/infrastructure/database/models/stock_model.py`)
**現状**: 
- `stocks` テーブルを定義
- 株式銘柄の基本情報を格納（ティッカーシンボル、会社名、市場、セクターなど）
- `StockRepositoryImpl` で使用されている

**判定**: **削除候補**
- J-Quants API の `ListedInfo` エンティティと重複する情報を持つ
- 現在のアーキテクチャでは `ListedInfo` が主要な銘柄情報源となっている
- ticker_symbol は J-Quants の code と重複

#### 1.2 PriceModel (`app/infrastructure/database/models/stock_model.py`)
**現状**:
- `prices` テーブルを定義
- 株価の時系列データを格納（OHLCV + adjusted_close）
- 現在どこからも参照されていない

**判定**: **削除対象**
- 価格データの永続化が現在の要件に含まれていない
- リポジトリ実装が存在しない
- J-Quants API から必要に応じて取得する設計になっている

#### 1.3 ListedInfoModel (`app/infrastructure/database/models/listed_info_model.py`)
**現状**:
- `listed_info` テーブルを定義
- J-Quants API の上場銘柄情報を格納
- `ListedInfoRepositoryImpl` で使用されている
- 日付とコードの複合主キー

**判定**: **保持**
- 現在アクティブに使用されている
- J-Quants API のデータをキャッシュする重要な役割

### 2. ドメインエンティティ

#### 2.1 Stock エンティティ (`app/domain/entities/stock.py`)
**現状**:
- StockCode 、 MarketCode 、 SectorCode17 、 SectorCode33 などの Enum を含む
- StockList バリューオブジェクトも定義

**判定**: **削除対象**
- ListedInfo エンティティと機能が重複
- 現段階では不要
- Enum の定義は有用なので別ファイルに移動すべき

#### 2.2 Price エンティティ (`app/domain/entities/price.py`)
**現状**:
- 株価データを表現するエンティティ
- TickerSymbol を使用
- 価格計算のプロパティを持つ

**判定**: **削除対象**
- 現段階では価格データの永続化要件がない
- TickerSymbol も削除対象のため依存関係の問題もある

#### 2.3 ListedInfo エンティティ (`app/domain/entities/listed_info.py`)
**現状**:
- J-Quants API のレスポンスに対応
- StockCode をインポートして使用

**判定**: **保持**
- 現在のメインエンティティとして機能

### 3. リポジトリ実装

#### 3.1 StockRepositoryImpl (`app/infrastructure/database/repositories/stock_repository_impl.py`)
**現状**:
- StockModel を使用した CRUD 操作を実装
- TickerSymbol バリューオブジェクトを使用

**判定**: **削除対象**
- StockModel が削除対象のため不要

### 4. バリューオブジェクト

#### 4.1 TickerSymbol (`app/domain/value_objects/ticker_symbol.py`)
**現状**:
- 株式のティッカーシンボルを表現

**判定**: **削除候補**
- StockCode と重複する概念
- J-Quants API では code を使用

## 削除対象リスト

### 即座に削除可能
1. `app/infrastructure/database/models/stock_model.py` の PriceModel クラス
2. `app/infrastructure/database/repositories/stock_repository_impl.py`
3. `app/domain/value_objects/ticker_symbol.py`
4. `app/domain/entities/price.py`
5. `app/domain/entities/stock.py` （Enum は別ファイルへ移動後）

### リファクタリング後に削除
1. `app/infrastructure/database/models/stock_model.py` の StockModel クラス

### 保持するもの
1. `app/infrastructure/database/models/listed_info_model.py`
2. `app/domain/entities/listed_info.py`
3. `app/domain/entities/stock.py` の各種 Enum 定義（MarketCode 、 SectorCode17 、 SectorCode33） - 別ファイルへ移動

## 推奨アクション

1. **フェーズ 1: 即座の削除**
   - PriceModel の削除
   - 関連するマイグレーションファイルの作成
   - StockRepositoryImpl の削除
   - TickerSymbol の削除と参照箇所の修正

2. **フェーズ 2: Enum の移動**
   - `app/domain/value_objects/market_codes.py` を作成
   - MarketCode 、 SectorCode17 、 SectorCode33 を移動
   - インポートパスの更新

3. **フェーズ 3: StockModel の削除**
   - StockModel を使用している箇所の確認と修正
   - マイグレーションファイルの作成
   - テストの更新

## 影響範囲

### マイグレーション
- `stocks` テーブルの削除
- `prices` テーブルの削除

### コードの修正が必要な箇所
- StockModel を参照している全ての箇所
- TickerSymbol を使用している箇所
- Stock/StockList エンティティを使用している箇所
- Price エンティティを使用している箇所
- stock.py の Enum をインポートしている箇所（新しいパスへ更新）

### テストの更新
- 削除されるモデル・リポジトリに関連するテストの削除
- 統合テストの見直し