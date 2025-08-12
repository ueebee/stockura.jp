# 複数データソース対応アーキテクチャ設計（フェーズ 1: ディレクトリ構成）

## 概要
要件 1 「ディレクトリ構成の明確化」のみを実装する設計。
データソースごとに独立したディレクトリ構造を作成し、将来的な拡張に備える。

## 現状の構成
```
app/infrastructure/external_services/
└── jquants/
    ├── __init__.py
    ├── base_client.py
    ├── client_factory.py
    ├── listed_info_client.py
    ├── types/
    │   ├── __init__.py
    │   └── responses.py
    └── mappers/
        ├── __init__.py
        └── listed_info_mapper.py
```

## 新しいディレクトリ構成

### 1. yfinance ディレクトリの追加
```
app/infrastructure/external_services/
├── jquants/  # 既存（変更なし）
│   ├── __init__.py
│   ├── base_client.py
│   ├── client_factory.py
│   ├── listed_info_client.py
│   ├── types/
│   │   ├── __init__.py
│   │   └── responses.py
│   └── mappers/
│       ├── __init__.py
│       └── listed_info_mapper.py
└── yfinance/  # 新規追加
    ├── __init__.py
    ├── base_client.py  # yfinance 用の基底クライアント
    ├── stock_info_client.py  # 株式情報取得クライアント
    ├── types/
    │   ├── __init__.py
    │   └── responses.py  # yfinance のレスポンス型定義
    └── mappers/
        ├── __init__.py
        └── stock_info_mapper.py  # yfinance データのマッパー
```

### 2. 各ファイルの役割

#### yfinance/__init__.py
- パッケージ初期化
- 主要なクラスのエクスポート

#### yfinance/base_client.py
- yfinance API の基底クライアント
- 共通のエラーハンドリング
- リトライ機構（必要に応じて）

#### yfinance/stock_info_client.py
- 株式情報取得の具体的な実装
- yfinance ライブラリのラッパー

#### yfinance/types/responses.py
- yfinance から返されるデータの型定義
- TypedDict または Pydantic モデルで定義

#### yfinance/mappers/stock_info_mapper.py
- yfinance のデータをドメインモデルへ変換
- 将来的には yfinance 固有のエンティティへ変換

## 実装の優先順位
1. ディレクトリ構造の作成
2. 各__init__.py ファイルの作成
3. 基本的なスケルトンコードの配置
4. README またはドキュメントの追加（各データソースの使い方）

## 利点
- データソースの追加が容易
- 各データソースのコードが独立
- 将来的な拡張（Alpha Vantage 等）のテンプレートとなる
- 既存の J-Quants コードに影響なし

## 注意事項
- この段階では実際の yfinance 実装は最小限
- ディレクトリ構造の確立が主目的
- 後続のフェーズで実装を充実させる