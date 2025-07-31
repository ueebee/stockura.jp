# ユニットテスト充実化 実装計画書

## 1. 実装概要

本実装計画では、テストカバレッジを 42.09% から 80% 以上に向上させるため、段階的にテストを修正・追加します。

## 2. 実装フェーズ

### フェーズ 1: 既存テストの修正（優先度: 最高）

#### 1.1 修正対象ファイル
1. `tests/unit/infrastructure/jquants/test_auth_repository.py`
2. `tests/unit/infrastructure/jquants/test_jquants_auth_repository.py`
3. `tests/unit/infrastructure/redis/test_redis_auth_repository.py`

#### 1.2 修正内容
- aiohttp の ClientSession モックを適切に設定
- 非同期コンテキストマネージャーの正しい実装
- レスポンスステータスコードの修正

#### 1.3 作業手順
1. 共通のモックヘルパー関数を作成
2. 各テストファイルのモック設定を更新
3. テスト実行して動作確認

### フェーズ 2: 共通ユーティリティの作成（優先度: 高）

#### 2.1 作成ファイル
1. `tests/utils/mock_helpers.py` - モック作成ヘルパー
2. `tests/factories/schedule_factory.py` - スケジュールテストデータ
3. `tests/factories/task_log_factory.py` - タスクログテストデータ

#### 2.2 実装内容
- 非同期 HTTP レスポンスモックの標準化
- データベースセッションモックの共通化
- テストデータ生成の簡略化

### フェーズ 3: アプリケーション層テストの追加（優先度: 高）

#### 3.1 ManageScheduleUseCase のテスト
- ファイル: `tests/unit/application/use_cases/test_manage_schedule_use_case.py`
- テストケース数: 約 10 件
- カバレッジ向上予測: +5%

#### 3.2 実装する主要テストケース
1. スケジュール作成（正常系・異常系）
2. スケジュール取得（単一・複数）
3. スケジュール更新
4. スケジュール削除
5. 有効化・無効化

### フェーズ 4: インフラストラクチャ層テストの追加（優先度: 高）

#### 4.1 ScheduleRepository のテスト
- ファイル: `tests/unit/infrastructure/database/repositories/test_schedule_repository.py`
- テストケース数: 約 8 件
- カバレッジ向上予測: +8%

#### 4.2 TaskLogRepository のテスト
- ファイル: `tests/unit/infrastructure/database/repositories/test_task_log_repository.py`
- テストケース数: 約 6 件
- カバレッジ向上予測: +5%

### フェーズ 5: プレゼンテーション層テストの追加（優先度: 中）

#### 5.1 Schedule API エンドポイントのテスト
- ファイル: `tests/unit/presentation/api/v1/endpoints/test_schedules.py`
- テストケース数: 約 8 件
- カバレッジ向上予測: +10%

#### 5.2 Auth API エンドポイントの補完
- 既存ファイルに追加
- テストケース数: 約 3 件
- カバレッジ向上予測: +3%

## 3. 実装順序と時間見積もり

| フェーズ | 作業内容 | 見積時間 | カバレッジ向上 |
|---------|----------|----------|----------------|
| 1 | 既存テスト修正 | 30 分 | +0%（修正のみ） |
| 2 | 共通ユーティリティ | 20 分 | +0%（基盤作成） |
| 3 | UseCase テスト | 40 分 | +5% |
| 4 | Repository テスト | 60 分 | +13% |
| 5 | API テスト | 40 分 | +13% |
| **合計** | | **約 3 時間** | **+31%** |

## 4. 実装の詳細手順

### Step 1: 既存テストの修正
```python
# tests/utils/mock_helpers.py を作成
class AsyncMockHelpers:
    @staticmethod
    def create_aiohttp_mock_response(status_code, json_data):
        mock_response = AsyncMock()
        mock_response.status = status_code
        mock_response.json = AsyncMock(return_value=json_data)
        return mock_response
    
    @staticmethod
    def create_aiohttp_session_mock():
        mock_session = AsyncMock()
        return mock_session
```

### Step 2: テストファイルの修正パターン
```python
# 修正前
with patch("app.infrastructure.jquants.auth_repository_impl.ClientSession") as mock:
    # 不適切なモック設定

# 修正後
with patch("aiohttp.ClientSession") as mock_session_class:
    mock_session = AsyncMockHelpers.create_aiohttp_session_mock()
    mock_response = AsyncMockHelpers.create_aiohttp_mock_response(200, {"refreshToken": "token"})
    
    mock_post = AsyncMock()
    mock_post.__aenter__.return_value = mock_response
    mock_session.post.return_value = mock_post
    mock_session_class.return_value = mock_session
```

### Step 3: 新規テストの追加パターン
```python
# ManageScheduleUseCase のテスト例
class TestManageScheduleUseCase:
    @pytest.fixture
    def mock_schedule_repository(self):
        return AsyncMock(spec=ScheduleRepository)
    
    @pytest.fixture
    def use_case(self, mock_schedule_repository, mock_task_log_repository):
        return ManageScheduleUseCase(
            schedule_repository=mock_schedule_repository,
            task_log_repository=mock_task_log_repository
        )
    
    @pytest.mark.asyncio
    async def test_create_schedule_success(self, use_case, mock_schedule_repository):
        # Arrange
        dto = ScheduleCreateDto(name="test", task_name="test_task", cron_expression="0 0 * * *")
        expected_schedule = ScheduleFactory.create_schedule_entity(name="test")
        mock_schedule_repository.create.return_value = expected_schedule
        
        # Act
        result = await use_case.create_schedule(dto)
        
        # Assert
        assert result.name == "test"
        mock_schedule_repository.create.assert_called_once()
```

## 5. 検証方法

### 5.1 各フェーズ完了時の検証
```bash
# フェーズ 1 完了後
pytest tests/unit/infrastructure/ -v

# フェーズ 3 完了後
pytest tests/unit/application/use_cases/test_manage_schedule_use_case.py -v

# 全体のカバレッジ確認
pytest --cov=app --cov-report=term-missing tests/unit/
```

### 5.2 最終検証
1. すべてのテストが成功すること
2. カバレッジが 80% 以上になること
3. 実行時間が 5 分以内であること

## 6. リスクと対策

### 6.1 想定されるリスク
- モックの複雑化による保守性の低下
- テスト実行時間の増加
- 依存関係の変更による既存テストへの影響

### 6.2 対策
- 共通ユーティリティによるモックの標準化
- 並列実行可能なテスト設計
- 段階的な実装と検証

## 7. 成功基準
- [ ] 失敗中の 9 テストがすべて成功
- [ ] カバレッジ 80% 以上達成
- [ ] 新規追加テストがすべて成功
- [ ] テスト実行時間 5 分以内