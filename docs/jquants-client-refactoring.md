# J-Quantsクライアント クリーンアーキテクチャ化

## 概要

J-QuantsクライアントをSOLIDの原則に基づいたクリーンアーキテクチャに再設計しました。この改善により、テスタビリティ、保守性、拡張性が大幅に向上しています。

## 主な改善点

### 1. レイヤー分離
- **ドメイン層**: インターフェース、DTO、例外の定義
- **インフラ層**: HTTP通信、認証、API実装
- **アプリケーション層**: 既存サービスとの統合

### 2. 依存性の逆転
- インターフェースを使用した抽象化
- 依存性注入によるテスタビリティの向上
- モック可能な設計

### 3. 自動リトライ機構
- 指数バックオフによるリトライ
- リトライ可能なエラーの自動判定
- カスタマイズ可能なリトライ設定

### 4. 統一されたエラーハンドリング
- カスタム例外クラスの階層
- 一貫性のあるエラー処理
- 詳細なエラー情報の提供

## アーキテクチャ

```
app/
├── domain/                      # ドメイン層
│   ├── interfaces/             # インターフェース定義
│   │   ├── api_client.py      # APIクライアントインターフェース
│   │   ├── authentication.py  # 認証インターフェース
│   │   └── rate_limiter.py    # レート制限インターフェース
│   ├── dto/                    # データ転送オブジェクト
│   │   ├── company.py         # 企業情報DTO
│   │   └── daily_quote.py     # 株価データDTO
│   └── exceptions/             # カスタム例外
│       └── jquants_exceptions.py
│
├── infrastructure/             # インフラ層
│   ├── http/                  # HTTP通信
│   │   ├── client.py         # 汎用HTTPクライアント
│   │   └── retry_handler.py  # リトライハンドラー
│   ├── auth/                  # 認証
│   │   └── jquants_auth_service.py
│   └── jquants/               # J-Quants API実装
│       ├── api_client.py      # APIクライアント実装
│       ├── request_builder.py # リクエスト構築
│       ├── response_parser.py # レスポンス解析
│       └── factory.py         # ファクトリー
│
└── services/                   # サービス層
    └── jquants_client.py      # J-Quantsクライアント管理
```

## 使用方法

### 1. 既存コードからの使用（互換性あり）

```python
from app.services.jquants_client import JQuantsClientManager

# クライアントマネージャーを作成
client_manager = JQuantsClientManager(data_source_service)
client = await client_manager.get_client(data_source_id)

# 既存のインターフェースと同じ使い方
companies = await client.get_listed_info()
```

### 2. 新しいAPIを直接使用

```python
from app.infrastructure.jquants import JQuantsClientFactory

# ファクトリーを使用してクライアントを作成
api_client = await JQuantsClientFactory.create(
    data_source_service=data_source_service,
    data_source_id=data_source_id
)

# 新しいインターフェースを使用
companies = await api_client.get_listed_companies(
    code="7203",
    target_date=date.today()
)
```

## 移行戦略

### Phase 1: 並行実装（完了）
- 新アーキテクチャの実装

### Phase 2: 完全移行（完了）
- 新アーキテクチャへの移行完了
- 旧実装の削除
- フィーチャーフラグの廃止

## テスト

```bash
# ユニットテスト実行
pytest tests/unit/infrastructure/

# 統合テスト実行
pytest tests/integration/jquants/

# カバレッジレポート
pytest --cov=app.infrastructure --cov=app.domain
```

## パフォーマンス改善

- **リトライ機構**: ネットワークエラー時の自動復旧
- **コネクションプーリング**: HTTP接続の再利用
- **非同期処理**: 並行リクエストの効率化

## 今後の拡張

1. **キャッシュ機能**: 頻繁にアクセスするデータのキャッシュ
2. **メトリクス収集**: API利用状況の監視
3. **他のAPIプロバイダー**: Yahoo Finance等への拡張