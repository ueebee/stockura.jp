# ユニットテスト充実化 設計書

## 1. 設計方針

### 1.1 基本方針
- **実行コードは一切修正しない** - テストコードのみを追加・修正
- **モックを適切に使用** - 外部依存を完全に分離
- **独立性を保つ** - 各テストは他のテストに依存しない
- **可読性を重視** - テストコードも保守性を考慮

### 1.2 テスト戦略
1. **失敗中のテストの修正を最優先**
2. **ビジネスロジックの核となる部分から順次カバー**
3. **共通のテストユーティリティを作成して重複を削減**

## 2. 修正が必要な既存テスト

### 2.1 インフラストラクチャ層のモック問題

#### 問題の原因
現在失敗している 9 件のテストは、すべて HTTP クライアントのモックが不適切なために発生：
- `aiohttp.ClientSession`のモックが実際の HTTP リクエストをブロックできていない
- レスポンスのステータスコードが期待値と異なる（200 を期待しているのに 400 が返る）

#### 修正方針
```python
# 現在の問題のあるモック
with patch("app.infrastructure.jquants.auth_repository_impl.ClientSession") as mock_session_class:
    mock_session = create_mock_session_context(mock_response)
    mock_session_class.return_value.__aenter__.return_value = mock_session

# 修正後のモック方法
with patch("aiohttp.ClientSession") as mock_session_class:
    # セッションインスタンスのモック
    mock_session_instance = AsyncMock()
    mock_session_class.return_value = mock_session_instance
    
    # コンテキストマネージャーのモック
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"refreshToken": "test_token"})
    
    mock_post_context = AsyncMock()
    mock_post_context.__aenter__.return_value = mock_response
    mock_session_instance.post.return_value = mock_post_context
```

### 2.2 修正対象ファイル
1. `tests/unit/infrastructure/jquants/test_auth_repository.py`
2. `tests/unit/infrastructure/jquants/test_jquants_auth_repository.py`
3. `tests/unit/infrastructure/redis/test_redis_auth_repository.py`

## 3. 新規テストの追加設計

### 3.1 アプリケーション層

#### ManageScheduleUseCase のテスト設計
```python
# tests/unit/application/use_cases/test_manage_schedule_use_case.py

class TestManageScheduleUseCase:
    # フィクスチャ
    - mock_schedule_repository
    - mock_task_log_repository
    - use_case_instance
    
    # テストケース
    - test_create_schedule_success
    - test_create_schedule_duplicate_name
    - test_get_schedule_success
    - test_get_schedule_not_found
    - test_get_all_schedules
    - test_update_schedule_success
    - test_delete_schedule_success
    - test_enable_schedule_success
    - test_disable_schedule_success
```

### 3.2 インフラストラクチャ層

#### ScheduleRepository のテスト設計
```python
# tests/unit/infrastructure/database/repositories/test_schedule_repository.py

class TestScheduleRepository:
    # フィクスチャ
    - mock_db_session
    - repository_instance
    - sample_schedule_entity
    - sample_db_schedule
    
    # テストケース
    - test_create_success
    - test_create_database_error
    - test_get_by_id_success
    - test_get_by_name_success
    - test_update_success
    - test_delete_success
    - test_entity_conversion
```

#### TaskLogRepository のテスト設計
```python
# tests/unit/infrastructure/database/repositories/test_task_log_repository.py

class TestTaskLogRepository:
    # テストケース
    - test_create_log
    - test_get_by_task_id
    - test_get_recent_logs_with_filters
    - test_update_status
```

### 3.3 プレゼンテーション層

#### Schedule API エンドポイントのテスト設計
```python
# tests/unit/presentation/api/v1/endpoints/test_schedules.py

class TestScheduleEndpoints:
    # フィクスチャ
    - mock_use_case
    - client (TestClient)
    
    # テストケース (各エンドポイント)
    - test_create_schedule_valid_request
    - test_create_schedule_invalid_request
    - test_list_schedules_with_filters
    - test_get_schedule_by_id
    - test_update_schedule
    - test_delete_schedule
    - test_enable_disable_schedule
```

## 4. 共通テストユーティリティの設計

### 4.1 モックヘルパー
```python
# tests/utils/mock_helpers.py

class MockHelpers:
    @staticmethod
    async def create_async_mock_response(status_code, json_data):
        """非同期 HTTP レスポンスのモックを作成"""
        
    @staticmethod
    def create_mock_db_session():
        """SQLAlchemy セッションのモックを作成"""
        
    @staticmethod
    def create_mock_redis_client():
        """Redis クライアントのモックを作成"""
```

### 4.2 テストデータファクトリー
```python
# tests/factories/

# schedule_factory.py
class ScheduleFactory:
    @staticmethod
    def create_schedule_entity(**kwargs):
        """Schedule エンティティを生成"""
        
    @staticmethod
    def create_schedule_dto(**kwargs):
        """ScheduleDTO を生成"""

# task_log_factory.py
class TaskLogFactory:
    @staticmethod
    def create_task_log(**kwargs):
        """TaskExecutionLog を生成"""
```

## 5. カバレッジ向上計画

### 5.1 フェーズ 1（優先度: 高）
- 失敗中の 9 テストを修正
- ManageScheduleUseCase のテスト追加
- ScheduleRepository のテスト追加

### 5.2 フェーズ 2（優先度: 中）
- TaskLogRepository のテスト追加
- Schedule API エンドポイントのテスト追加
- Auth API の残りのエンドポイントテスト追加

### 5.3 フェーズ 3（優先度: 低）
- CLI コマンドのテスト追加
- RedisClient のテスト追加

## 6. テスト実行計画

### 6.1 段階的実行
1. 修正したテストのみ実行して動作確認
2. 新規追加したテストを個別に実行
3. 全体テストを実行してカバレッジ確認

### 6.2 検証コマンド
```bash
# 個別テスト実行
pytest tests/unit/infrastructure/jquants/test_auth_repository.py -v

# カバレッジ付き実行
pytest --cov=app --cov-report=term-missing tests/unit/

# HTML カバレッジレポート生成
pytest --cov=app --cov-report=html tests/unit/
```

## 7. 期待される成果
- テストカバレッジ: 42.09% → 80% 以上
- すべてのテストが成功
- 新規機能追加時のリグレッション防止
- コードの品質向上と信頼性の確保