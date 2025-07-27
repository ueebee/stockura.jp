# Stockura ドキュメント

このディレクトリには、 Stockura プロジェクトのアーキテクチャと実装に関する詳細なドキュメントが含まれています。

## ドキュメント一覧

### 1. [ARCHITECTURE.md](./ARCHITECTURE.md)
プロジェクト全体のアーキテクチャ概要を説明しています。
- クリーンアーキテクチャの採用理由
- 各レイヤーの責務
- 主要コンポーネントの説明
- 技術スタックの詳細

### 2. [FILE_STRUCTURE.md](./FILE_STRUCTURE.md)
各ファイルの詳細な役割と実装内容を説明しています。
- Domain 層の各ファイルの詳細
- Application 層のユースケース実装
- Infrastructure 層の具体的な実装
- テストファイルの構成

### 3. [CLEAN_ARCHITECTURE_DIAGRAM.md](./CLEAN_ARCHITECTURE_DIAGRAM.md)
クリーンアーキテクチャのレイヤー構成を視覚的に表現しています。
- レイヤー間の依存関係図
- データフローの例
- 各レイヤーの責務の詳細
- 実装済みコンポーネントの関係図

## クイックリファレンス

### 現在の実装状況

#### ✅ 実装済み
- **Domain 層**: エンティティ、バリューオブジェクト、リポジトリインターフェース
- **Application 層**: 認証・銘柄情報のユースケース
- **Infrastructure 層**: J-Quants API 連携、キャッシュ機能
- **テスト**: エンティティとユースケースの単体テスト

#### 🚧 未実装
- **Presentation 層**: FastAPI エンドポイント、スキーマ定義
- **Infrastructure 層**: データベース連携、 Redis キャッシュ
- **設定**: 環境変数、依存性注入の設定

### 主要な機能

1. **J-Quants API 認証**
   - リフレッシュトークンと ID トークンの管理
   - 自動的なトークン更新

2. **銘柄情報管理**
   - 全銘柄一覧の取得とキャッシュ
   - 銘柄コード、市場区分、業種での検索
   - 会社名での検索（日本語・英語対応）

### ディレクトリマップ

```
app/
├── domain/           # ビジネスロジックの中核
│   ├── entities/     # Stock, JQuantsCredentials
│   ├── repositories/ # 抽象インターフェース
│   └── exceptions/   # ドメイン固有の例外
├── application/      # ユースケース実装
│   └── use_cases/    # AuthUseCase, StockUseCase
├── infrastructure/   # 外部連携の実装
│   └── jquants/      # J-Quants API 実装
└── presentation/     # API 層（未実装）
```

## 開発ガイドライン

### 新機能追加時の手順

1. **Domain 層**: 必要なエンティティやバリューオブジェクトを定義
2. **Repository Interface**: データアクセスの抽象を定義
3. **Use Case**: ビジネスロジックを実装
4. **Infrastructure**: リポジトリの具体的な実装
5. **Presentation**: API エンドポイントを追加
6. **Test**: 各レイヤーのテストを作成

### コーディング規約

- **命名規則**: PEP 8 に準拠
- **型ヒント**: 全ての関数に型アノテーションを付ける
- **非同期処理**: async/await を積極的に使用
- **エラーハンドリング**: ドメイン固有の例外を使用
- **テスト**: pytest を使用し、カバレッジ 80% 以上を目標

## 参考リンク

- [J-Quants API 仕様書](https://jpx.gitbook.io/j-quants-ja/api-reference)
- [FastAPI ドキュメント](https://fastapi.tiangolo.com/)
- [クリーンアーキテクチャ](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)