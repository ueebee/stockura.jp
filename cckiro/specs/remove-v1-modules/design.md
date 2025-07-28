# v2 移行済み旧モジュール削除の設計

## 概要
v2 に移行が完了した旧モジュール（stock_old.py 、 price_old.py）を安全に削除する設計

## 現状分析

### 対象ファイル
1. `app/domain/entities/stock_old.py`
   - 旧 Stock エンティティの実装
   - dataclass ベースの実装
   - TickerSymbol を使用

2. `app/domain/entities/price_old.py`
   - 旧 Price エンティティの実装
   - dataclass ベースの実装
   - Decimal を使用した価格管理

### 新バージョンとの比較
- **stock.py**: J-Quants API に準拠した新しい実装
  - StockCode バリューオブジェクト（4 桁の銘柄コード）
  - MarketCode 、 SectorCode などの Enum 定義
  - より詳細な銘柄情報の管理

- **旧実装との違い**:
  - 命名規則: 英語 → 日本語（J-Quants API に準拠）
  - データ構造: より詳細な業種分類（17 業種、 33 業種）
  - バリューオブジェクト: TickerSymbol → StockCode

### 依存関係調査結果
- stock_old.py への参照: **なし**
- price_old.py への参照: **なし**
- テストコードからの参照: **なし**

## 削除設計

### 削除対象
1. ファイル本体
   - `app/domain/entities/stock_old.py`
   - `app/domain/entities/price_old.py`

2. 関連ファイル（自動生成）
   - `htmlcov/z_3efee37c27925ae3_stock_old_py.html`
   - `htmlcov/z_3efee37c27925ae3_price_old_py.html`

### 削除手順
1. **事前確認**
   - 現在のテストがすべて通ることを確認
   - アプリケーションが正常に起動することを確認

2. **ファイル削除**
   - 旧エンティティファイルを削除
   - カバレッジレポートの関連ファイルを削除

3. **事後確認**
   - テストの再実行
   - アプリケーションの動作確認
   - import エラーがないことの確認

### リスク評価
- **リスクレベル**: 低
- **理由**: 
  - 依存関係調査で参照が見つからない
  - 新実装が既に稼働している
  - 削除は可逆的（git で復元可能）

## 実装後の状態
- `app/domain/entities/`ディレクトリがよりクリーンに
- 新旧の混在による混乱を防止
- J-Quants API 準拠の実装のみが残る

## ロールバック計画
万が一問題が発生した場合：
1. `git checkout HEAD -- app/domain/entities/stock_old.py`
2. `git checkout HEAD -- app/domain/entities/price_old.py`
で即座に復元可能