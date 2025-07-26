# 設計ファイル：Celeryタスクの引数受け渡し方法の統一

## 設計方針

### 統一方法
すべてのスケジュールタスクで**kwargs（キーワード引数）**を使用することで統一する。

#### 選定理由
1. **明示性**: 引数名が明確で、何を渡しているかが分かりやすい
2. **拡張性**: 新しいパラメータを追加しても既存コードへの影響が少ない
3. **デフォルト値**: オプション引数の扱いが容易
4. **Celeryの推奨**: Celeryドキュメントでもkwargsの使用が推奨されている

## 設計詳細

### 1. タスク定義の統一パターン

```python
@celery_app.task(bind=True, name="task_name")
def scheduled_task(self, **kwargs):
    """
    スケジュール実行用タスク
    
    Kwargs:
        param1 (type): 説明
        param2 (type, optional): 説明. Defaults to value.
    """
    # パラメータの取得（デフォルト値付き）
    param1 = kwargs.get('param1')
    param2 = kwargs.get('param2', 'default_value')
    
    # 処理実装
    ...
```

### 2. 変更対象

#### A. sync_daily_quotes_scheduled（修正が必要）
**現状**:
```python
def sync_daily_quotes_scheduled(
    self,
    schedule_id: int,
    sync_type: str,
    data_source_id: int,
    relative_preset: Optional[str] = None
)
```

**変更後**:
```python
def sync_daily_quotes_scheduled(self, **kwargs)
```

内部でkwargsから必要なパラメータを取得する。

#### B. sync_listed_companies（スケジューラー設定の修正が必要）
**現状**（celery_beat_init.py）:
```python
'args': ['scheduled'],
```

**変更後**:
```python
'kwargs': {'execution_type': 'scheduled'},
```

### 3. スケジューラー設定の統一

#### RedBeat（daily_quotes_schedule_service.py）
現状のまま（既にkwargsを使用）:
```python
kwargs={
    'schedule_id': schedule.id,
    'sync_type': schedule.sync_type,
    'data_source_id': schedule.data_source_id,
    'relative_preset': schedule.relative_preset
}
```

#### Celery Beat（celery_beat_init.py）
argsからkwargsに変更:
```python
schedules[schedule_name] = {
    'task': 'sync_listed_companies',
    'schedule': crontab(...),
    'kwargs': {'execution_type': 'scheduled'},  # argsから変更
    'options': {...}
}
```

### 4. 後方互換性の考慮

開発中のため既存のスケジュールは考慮不要とのことなので、クリーンな実装が可能。

### 5. エラーハンドリング

必須パラメータが渡されない場合の処理:
```python
def scheduled_task(self, **kwargs):
    # 必須パラメータのチェック
    required_params = ['param1', 'param2']
    missing_params = [p for p in required_params if p not in kwargs]
    
    if missing_params:
        raise ValueError(f"Missing required parameters: {missing_params}")
```

### 6. ドキュメント化

各タスクには以下の情報を含むdocstringを記載:
- タスクの概要
- Kwargsセクションで各パラメータを説明
- 戻り値の説明

## テスト戦略

1. **単体テスト**: 各タスクがkwargsを正しく処理することを確認
2. **統合テスト**: スケジューラーからの呼び出しが正常に動作することを確認
3. **パラメータテスト**: 必須/オプションパラメータの動作確認

## 移行計画

1. sync_daily_quotes_scheduledの引数定義を変更
2. celery_beat_init.pyのsync_listed_companiesの設定を変更
3. テストの実行と動作確認
4. ドキュメントの更新