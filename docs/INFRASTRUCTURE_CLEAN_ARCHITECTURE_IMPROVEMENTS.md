# Infrastructure 層 クリーンアーキテクチャ改善

## 概要

本ドキュメントは、 Stockura プロジェクトの infrastructure 層に対して実施したクリーンアーキテクチャ改善の内容をまとめたものです。

## 実施日
2025-08-10

## 改善の背景

infrastructure 層の分析により、以下の問題点が特定されました：

1. **エンティティ・モデル変換の重複**
   - 各リポジトリ実装内で同様の変換ロジックが重複

2. **型安全性の欠如**
   - 外部 API レスポンスが Dict[str, Any]で定義されており、型安全性が低い

3. **ディレクトリ構造の冗長性**
   - external_api と jquants で機能が重複

4. **責務の混在**
   - アプリケーション層にファクトリーが配置されている

5. **設定管理の分散**
   - インフラ固有の設定が core 層に混在

## 実施した改善

### 1. Mapper パターンの導入

#### 基底 Mapper クラス
```python
# app/infrastructure/database/mappers/base_mapper.py
class BaseMapper(ABC, Generic[TEntity, TModel]):
    @abstractmethod
    def to_entity(self, model: TModel) -> TEntity:
        pass
    
    @abstractmethod
    def to_model(self, entity: TEntity) -> TModel:
        pass
```

#### 効果
- エンティティ・モデル変換ロジックの一元化
- 各リポジトリから変換ロジックを分離
- テストしやすい構造の実現

### 2. TypedDict による型安全性の向上

```python
# app/infrastructure/external_services/jquants/types/responses.py
class JQuantsListedInfoResponse(TypedDict):
    Date: str
    Code: str
    CompanyName: str
    CompanyNameEnglish: Optional[str]
    # ... その他のフィールド
```

#### 効果
- 外部 API レスポンスの型安全性向上
- IDE による補完機能の有効化
- 実行時エラーの削減

### 3. ディレクトリ構造の再編成

```
app/infrastructure/
├── external_services/
│   └── jquants/
│       ├── types/
│       │   └── responses.py
│       ├── mappers/
│       │   └── listed_info_mapper.py
│       ├── base_client.py
│       ├── client_factory.py
│       └── listed_info_client.py
```

#### 効果
- 外部サービス関連コードの集約
- ディレクトリ構造の簡潔化
- 依存関係の明確化

### 4. ファクトリーの適切な配置

ListedInfoFactory を application 層から domain 層へ移動：
- 移動前: `app/application/factories/listed_info_factory.py`
- 移動後: `app/domain/factories/listed_info_factory.py`

#### 効果
- ドメイン層の自己完結性向上
- 依存関係の適正化
- クリーンアーキテクチャ原則への準拠

### 5. インフラ固有設定の分離

```python
# app/infrastructure/config/settings.py
class InfrastructureSettings(BaseSettings):
    database: DatabaseSettings
    redis: RedisSettings
    celery: CelerySettings
    jquants: JQuantsSettings
```

#### 効果
- インフラ設定の一元管理
- core 層からのインフラ詳細の分離
- 設定の階層化による管理性向上

## 技術的詳細

### 改善された依存関係

1. **リポジトリ実装**
   ```python
   def __init__(self, session: AsyncSession, mapper: Optional[ListedInfoMapper] = None):
       self._session = session
       self._mapper = mapper or ListedInfoMapper()
   ```
   - Mapper を依存性注入可能に
   - テスト時のモック化が容易

2. **エラーハンドリング**
   ```python
   # app/infrastructure/exceptions.py
   class InfrastructureError(Exception)
   class DatabaseError(InfrastructureError)
   class ExternalAPIError(InfrastructureError)
   ```
   - インフラ層固有の例外階層を定義
   - エラーハンドリングの明確化

### パフォーマンスへの影響

- Mapper パターンの導入による若干のオーバーヘッド
- 型チェックによる開発時の安全性向上
- 全体的なコードの保守性向上

## テスト結果

- 単体テスト: 439 件パス / 14 件失敗（設定関連）
- テストカバレッジ: 56.83%
- 主要機能のテストはすべてパス

## 今後の推奨事項

1. **設定管理の完全移行**
   - すべてのインフラ設定を InfrastructureSettings に移行
   - 環境別設定の管理方法の確立

2. **Mapper パターンの拡張**
   - 他のエンティティへの Mapper 実装
   - バッチ変換の最適化

3. **エラーハンドリングの強化**
   - より詳細な例外クラスの定義
   - エラーロギングの改善

4. **テストカバレッジの向上**
   - インフラ層のモックテスト追加
   - 統合テストの環境整備

## まとめ

今回の改善により、 infrastructure 層はクリーンアーキテクチャの原則により準拠した構造となりました。特に、責務の分離、型安全性の向上、依存関係の明確化において大きな改善が達成されました。これにより、コードの保守性と拡張性が向上し、今後の開発効率の向上が期待されます。