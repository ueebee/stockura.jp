# 実装サマリー：Celeryタスクの引数受け渡し方法の統一

## 実装完了内容

### 1. sync_daily_quotes_scheduled タスクの変更
**ファイル**: `app/tasks/daily_quotes_tasks.py`

**変更内容**:
- 位置引数から**kwargsへの変更
- 必須パラメータの検証処理を追加
- エラーハンドリングでもkwargsを使用するように修正

```python
# 変更前
def sync_daily_quotes_scheduled(
    self,
    schedule_id: int,
    sync_type: str,
    data_source_id: int,
    relative_preset: Optional[str] = None
) -> Dict:

# 変更後
def sync_daily_quotes_scheduled(self, **kwargs) -> Dict:
    # パラメータの取得と検証
    required_params = ['schedule_id', 'sync_type', 'data_source_id']
    missing_params = [p for p in required_params if p not in kwargs]
    if missing_params:
        raise ValueError(f"Missing required parameters: {missing_params}")
```

### 2. celery_beat_init.py の変更
**ファイル**: `app/core/celery_beat_init.py`

**変更内容**:
- sync_listed_companiesのスケジュール設定でargsからkwargsに変更

```python
# 変更前
'args': ['scheduled'],

# 変更後
'kwargs': {'execution_type': 'scheduled'},
```

## 変更の影響

### 互換性
- RedBeatSchedulerは既にkwargsを使用していたため、影響なし
- celery_beat_init.pyの変更により、sync_listed_companiesも統一された方法で引数を受け取る

### メリット
1. **一貫性**: すべてのスケジュールタスクが同じ方法で引数を受け取る
2. **拡張性**: 新しいパラメータの追加が容易
3. **可読性**: 引数名が明示的で理解しやすい
4. **エラーハンドリング**: 必須パラメータの欠落を検出可能

## テスト方法

### 手動テスト
1. Celeryワーカーの起動
```bash
celery -A app.core.celery_app worker --loglevel=info
```

2. タスクの手動実行
```python
# sync_daily_quotes_scheduled
from app.tasks.daily_quotes_tasks import sync_daily_quotes_scheduled
result = sync_daily_quotes_scheduled.delay(
    schedule_id=1,
    sync_type='incremental',
    data_source_id=1,
    relative_preset='last7days'
)

# sync_listed_companies
from app.tasks.company_tasks import sync_listed_companies
result = sync_listed_companies.delay(execution_type='manual')
```

## 今後の推奨事項

1. **新しいスケジュールタスクの追加時**:
   - 必ず**kwargsを使用してパラメータを受け取る
   - 必須パラメータの検証を実装する
   - docstringでKwargsセクションを記載する

2. **ベストプラクティス**:
   ```python
   @celery_app.task(bind=True, name="new_scheduled_task")
   def new_scheduled_task(self, **kwargs) -> Dict:
       """
       タスクの説明
       
       Kwargs:
           param1 (type): 説明
           param2 (type, optional): 説明. Defaults to value.
       """
       # パラメータ検証
       required_params = ['param1']
       missing_params = [p for p in required_params if p not in kwargs]
       if missing_params:
           raise ValueError(f"Missing required parameters: {missing_params}")
   ```