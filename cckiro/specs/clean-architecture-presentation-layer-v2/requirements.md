# presentation 層のクリーンアーキテクチャ改善要件（第 2 回）

## 背景

第 1 回の改善で、 presentation 層の依存性注入プロバイダーを集約し、インフラストラクチャ層への直接的な依存を大幅に削減しました。第 2 回では、 CLI 層に残された依存性の問題を解決します。

## 現状の課題

### CLI 層の依存性問題
- CLI コマンドがインフラストラクチャ層に直接依存している
- 依存性注入の仕組みが API 層と CLI 層で異なる
- 特に`fetch_listed_info_command.py`と`migration_command.py`が問題

具体的な問題点：
1. `fetch_listed_info_command.py`
   - インフラストラクチャ層のクライアントやリポジトリを直接インポート・インスタンス化
   - JQuantsBaseClient 、 JQuantsListedInfoClient 、 JQuantsAuthRepository などの実装に直接依存
   - get_async_session_context を直接使用

2. `migration_command.py`
   - インフラストラクチャ層のマイグレーション関数を直接インポート
   - データベース操作の実装に直接依存

## 要件

### CLI 層の依存性注入の改善
1. **依存性プロバイダーの作成**
   - `presentation/dependencies/cli.py` を新規作成
   - CLI コマンド用の依存性注入関数を実装
   - API 層と同様の DI パターンを採用

2. **CLI コマンドのリファクタリング**
   - `fetch_listed_info_command.py` の改善
     - インフラストラクチャ層への直接インポートを削除
     - 依存性注入を使用してサービスやリポジトリを取得
     - ビジネスロジックは use case 層に移動
   
   - `migration_command.py` の改善
     - マイグレーション機能のインターフェース化を検討
     - 最小限の変更で依存性を削減

3. **共通インターフェースの活用**
   - ドメイン層で定義されたインターフェースのみに依存
   - 実装の詳細は依存性注入で解決

## 制約条件

- 既存の CLI コマンドの動作は変更しない（後方互換性を維持）
- テストが全て通る状態を維持する
- 段階的に改善を行い、各段階で動作確認を行う
- ドメイン層とインフラストラクチャ層への変更は最小限に留める

## 成功基準

- CLI 層がインフラストラクチャ層に直接依存していないこと
- 依存性注入の仕組みが API 層と統一されていること
- 全てのテストが通ること
- CLI コマンドが正常に動作すること

## 実装計画

1. `presentation/dependencies/cli.py` の作成
2. `fetch_listed_info_command.py` のリファクタリング
3. `migration_command.py` のリファクタリング
4. テストの実行と動作確認