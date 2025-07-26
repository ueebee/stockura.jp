# 実装計画ファイル：Celeryタスクの引数受け渡し方法の統一

## 実装順序とタスク

### Phase 1: sync_daily_quotes_scheduledの修正（優先度：高）
1. **タスク定義の変更**
   - ファイル: `app/tasks/daily_quotes_tasks.py`
   - 関数: `sync_daily_quotes_scheduled`
   - 位置引数から**kwargsへの変更
   - 内部でkwargsからパラメータを取得する処理を追加

2. **パラメータ検証の追加**
   - 必須パラメータのチェック
   - エラーメッセージの改善

3. **ログ出力の調整**
   - パラメータ情報をログに含める

### Phase 2: sync_listed_companiesの修正（優先度：高）
1. **スケジューラー設定の変更**
   - ファイル: `app/core/celery_beat_init.py`
   - argsからkwargsへの変更
   - execution_typeをキーワード引数として渡す

2. **動作確認**
   - タスクが正しくexecution_typeを受け取ることを確認

### Phase 3: テストとドキュメント（優先度：中）
1. **テストの作成/修正**
   - sync_daily_quotes_scheduledのテスト修正
   - sync_listed_companiesのテスト確認

2. **ドキュメントの更新**
   - タスクのdocstring更新
   - 必要に応じてREADME更新

### Phase 4: 動作確認（優先度：高）
1. **ローカル環境での動作確認**
   - Celeryワーカーの起動
   - タスクの手動実行
   - スケジュール実行の確認

2. **ログの確認**
   - パラメータが正しく渡されているか
   - エラーが発生していないか

## 詳細な変更内容

### 1. sync_daily_quotes_scheduled（app/tasks/daily_quotes_tasks.py）

**変更前**:
```python
@celery_app.task(bind=True, name="sync_daily_quotes_scheduled")
def sync_daily_quotes_scheduled(
    self,
    schedule_id: int,
    sync_type: str,
    data_source_id: int,
    relative_preset: Optional[str] = None
) -> Dict:
```

**変更後**:
```python
@celery_app.task(bind=True, name="sync_daily_quotes_scheduled")
def sync_daily_quotes_scheduled(self, **kwargs) -> Dict:
    """
    定期実行用の株価データ同期タスク
    
    Kwargs:
        schedule_id (int): スケジュールID
        sync_type (str): 同期タイプ（full/incremental）
        data_source_id (int): データソースID
        relative_preset (str, optional): 相対日付プリセット（last7days等）
        
    Returns:
        Dict: 同期結果
    """
    # パラメータの取得と検証
    required_params = ['schedule_id', 'sync_type', 'data_source_id']
    missing_params = [p for p in required_params if p not in kwargs]
    if missing_params:
        raise ValueError(f"Missing required parameters: {missing_params}")
    
    schedule_id = kwargs['schedule_id']
    sync_type = kwargs['sync_type']
    data_source_id = kwargs['data_source_id']
    relative_preset = kwargs.get('relative_preset')
```

### 2. celery_beat_init.py（app/core/celery_beat_init.py）

**変更前**:
```python
schedules[schedule_name] = {
    'task': 'sync_listed_companies',
    'schedule': crontab(
        hour=utc_datetime.hour,
        minute=utc_datetime.minute
    ),
    'args': ['scheduled'],
    'options': {
        'queue': 'default',
        'expires': 3600,
    }
}
```

**変更後**:
```python
schedules[schedule_name] = {
    'task': 'sync_listed_companies',
    'schedule': crontab(
        hour=utc_datetime.hour,
        minute=utc_datetime.minute
    ),
    'kwargs': {'execution_type': 'scheduled'},
    'options': {
        'queue': 'default',
        'expires': 3600,
    }
}
```

## リスクと対策

### リスク
1. **既存のタスク実行への影響**
   - 対策: 開発環境で十分にテストを実施

2. **パラメータの不整合**
   - 対策: 必須パラメータのチェックを実装

3. **ログの欠落**
   - 対策: パラメータ情報を含むログ出力を追加

## 成功の判定基準
1. すべてのスケジュールタスクがkwargsで統一される
2. 既存の機能が正常に動作する
3. ログでパラメータの受け渡しが確認できる
4. エラー時に適切なメッセージが表示される