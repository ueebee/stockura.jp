# yfinance Data Source

このディレクトリには、 Yahoo Finance（yfinance）からデータを取得するためのコードが含まれています。

## ディレクトリ構成

```
yfinance/
├── __init__.py              # パッケージ初期化
├── base_client.py           # yfinance 基底クライアント
├── stock_info_client.py     # 株式情報取得クライアント
├── types/
│   ├── __init__.py
│   └── responses.py         # レスポンス型定義
└── mappers/
    ├── __init__.py
    └── stock_info_mapper.py # データマッパー
```

## 主要コンポーネント

### YfinanceBaseClient
- yfinance ライブラリのラッパー
- 基本的なデータ取得機能を提供
- エラーハンドリングとロギング

### YfinanceStockInfoClient
- 株式情報の取得に特化したクライアント
- 企業情報、価格データ、財務諸表などを取得
- 非同期対応（将来の拡張のため）

### 型定義（types/responses.py）
- `YfinanceStockInfo`: 基本的な株式情報
- `YfinanceHistoricalData`: 過去の価格データ
- `YfinanceFinancialStatement`: 財務諸表データ

### マッパー（mappers/stock_info_mapper.py）
- yfinance のデータを内部形式に変換
- 将来的にドメインモデルへのマッピングを実装

## 使用方法（実装予定）

```python
from app.infrastructure.external_services.yfinance.base_client import YfinanceBaseClient
from app.infrastructure.external_services.yfinance.stock_info_client import YfinanceStockInfoClient

# クライアントの初期化
async with YfinanceBaseClient() as base_client:
    client = YfinanceStockInfoClient(base_client)
    
    # 株式情報の取得
    stock_info = await client.get_stock_info("AAPL")
    
    # 過去データの取得
    historical_data = await client.get_historical_data(
        "AAPL",
        start_date="2024-01-01",
        end_date="2024-12-31"
    )
```

## 注意事項

1. **認証不要**: yfinance は Yahoo Finance の公開データを使用するため、認証は不要です
2. **レート制限**: Yahoo Finance には暗黙的なレート制限があるため、大量のリクエストは避けてください
3. **データの利用規約**: Yahoo Finance の利用規約に従ってください
4. **非同期対応**: 現在の yfinance ライブラリは同期的ですが、将来の拡張性のため非同期インターフェースを採用

## TODO

- [ ] 実際の yfinance ライブラリとの統合
- [ ] エラーハンドリングの強化
- [ ] キャッシング機能の実装
- [ ] バッチ処理の最適化
- [ ] ドメインモデルへのマッピング実装
- [ ] テストの追加