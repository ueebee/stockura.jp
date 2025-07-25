# CompanySyncService リファクタリング実装計画

## 1. 実装フェーズ

### Phase 1: インターフェースと新クラスの実装（既存コードは変更なし）

#### 1.1 インターフェース定義
- [ ] `app/services/interfaces/company_sync_interfaces.py` を作成
  - ICompanyDataFetcher
  - ICompanyDataMapper
  - ICompanyRepository

#### 1.2 新クラスの実装
- [ ] `app/services/company/company_data_fetcher.py` を作成
- [ ] `app/services/company/company_data_mapper.py` を作成
- [ ] `app/services/company/company_repository.py` を作成

#### 1.3 単体テストの作成
- [ ] `tests/unit/services/company/test_company_data_fetcher.py`
- [ ] `tests/unit/services/company/test_company_data_mapper.py`
- [ ] `tests/unit/services/company/test_company_repository.py`

### Phase 2: CompanySyncServiceの段階的リファクタリング

#### 2.1 新クラスの統合
- [ ] CompanySyncServiceのコンストラクタに新クラスを追加
- [ ] sync_companies メソッドを新実装に置き換え
- [ ] 古いメソッドを deprecated としてマーク

#### 2.2 統合テスト
- [ ] 既存のテストが全てパスすることを確認
- [ ] 新しい統合テストを追加

### Phase 3: クリーンアップ

#### 3.1 古いコードの削除
- [ ] deprecated メソッドの削除
- [ ] 不要なインポートの削除

#### 3.2 最終テスト
- [ ] 全テストスイートの実行
- [ ] パフォーマンステスト

## 2. 実装順序と詳細

### Step 1: インターフェース定義（30分）

```python
# app/services/interfaces/company_sync_interfaces.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from app.models.company import Company

class ICompanyDataFetcher(ABC):
    @abstractmethod
    async def fetch_all_companies(self) -> List[Dict[str, Any]]:
        """全企業データを取得"""
        pass
    
    @abstractmethod
    async def fetch_company_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """特定企業データを取得"""
        pass

class ICompanyDataMapper(ABC):
    @abstractmethod
    def map_to_model(self, api_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """APIデータをモデル用にマッピング"""
        pass
    
    @abstractmethod
    def validate_data(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """データ検証"""
        pass

class ICompanyRepository(ABC):
    @abstractmethod
    async def find_by_code(self, code: str) -> Optional[Company]:
        """銘柄コードで企業を検索"""
        pass
    
    @abstractmethod
    async def save(self, company_data: Dict[str, Any]) -> Company:
        """企業データを保存"""
        pass
    
    @abstractmethod
    async def bulk_upsert(self, companies: List[Dict[str, Any]]) -> Dict[str, int]:
        """企業データを一括更新"""
        pass
    
    @abstractmethod
    async def deactivate_companies(self, exclude_codes: List[str]) -> int:
        """指定コード以外の企業を非アクティブ化"""
        pass
```

### Step 2: CompanyDataFetcher実装（1時間）

既存のJQuantsClientManagerを活用：
- エラーハンドリングの改善
- リトライロジックの追加
- ログ出力の整理

### Step 3: CompanyDataMapper実装（45分）

純粋関数として実装：
- 既存の_map_jquants_data_to_modelロジックを移植
- データ検証の強化
- エラーメッセージの改善

### Step 4: CompanyRepository実装（1.5時間）

データベース操作の集約：
- トランザクション管理
- バルク操作の最適化
- エラーハンドリング

### Step 5: 単体テスト作成（2時間）

各クラスの単体テスト：
- モックを使用した独立したテスト
- エッジケースのカバー
- エラーケースのテスト

### Step 6: CompanySyncService統合（2時間）

新クラスを使用するように変更：
- 依存性注入の実装
- 段階的な置き換え
- 後方互換性の維持

### Step 7: 統合テストと検証（1時間）

- 既存テストの実行
- 新規統合テストの追加
- パフォーマンス測定

## 3. リスク管理

### 3.1 テスト戦略
1. 各ステップでテストを実行
2. カバレッジを常に確認
3. CI/CDパイプラインでの自動テスト

### 3.2 ロールバック計画
- 各フェーズごとにコミット
- 問題発生時は前のコミットに戻る
- feature flagの検討（必要に応じて）

## 4. 見積もり時間

- Phase 1: 5.5時間
- Phase 2: 3時間
- Phase 3: 1時間
- **合計: 約9.5時間**

## 5. 成果物

1. リファクタリングされたコード
2. 包括的な単体テスト
3. 更新されたドキュメント
4. パフォーマンス比較レポート

## 6. 進捗管理

- [ ] Phase 1 完了
- [ ] Phase 2 完了
- [ ] Phase 3 完了
- [ ] コードレビュー
- [ ] マージ準備完了