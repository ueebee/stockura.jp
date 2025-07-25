# Stockura - 株価データ分析プラットフォーム

## 概要
Stockura は、 J-Quants と yFinance から取得した株価データを統合的に管理・分析するためのプラットフォームです。日本株式市場のデータを中心に、グローバルな市場データも含めた包括的な分析環境を提供します。

## 主な機能
- **データ収集**: J-Quants API および yFinance からの自動データ取得
- **データ統合**: 異なるソースからのデータを一元管理
- **分析ツール**: 各種テクニカル指標の計算と可視化
- **API 提供**: FastAPI による RESTful API の提供
- **データストレージ**: PostgreSQL と Redis を使用した効率的なデータ管理

## 技術スタック
- **バックエンド**: Python, FastAPI
- **データベース**: PostgreSQL (時系列データ), Redis (キャッシュ)
- **JobQueue**: Celery(Beat)
- **アーキテクチャ**: クリーンアーキテクチャ
- **データソース**:
  - J-Quants API (日本株データ)
  - yFinance (日本株データ,グローバル市場データ)

## プロジェクト構造
```
stockura/
├── app/                    # アプリケーションコード
│   ├── api/               # API エンドポイント
│   ├── core/              # コア設定・共通処理
│   ├── domain/            # ドメインモデル
│   ├── infrastructure/    # 外部サービス連携
│   ├── services/          # ビジネスロジック
│   └── repositories/      # データアクセス層
├── tests/                 # テストコード
├── scripts/               # ユーティリティスクリプト
└── docs/                  # ドキュメント

```

## セットアップ
（今後追加予定）

## 使用方法
（今後追加予定）

## ライセンス
（今後追加予定）
