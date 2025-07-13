# タイムゾーン統一実装計画

## 現状の問題点

1. Celery Beatのスケジュールが明示的なタイムゾーン設定を持たない
2. アプリケーション全体でタイムゾーン処理が統一されていない
3. データベースとアプリケーションのタイムゾーンが暗黙的にUTCを使用

## 実装方針

### 基本方針
- **保存**: すべての時刻データはUTCで保存
- **表示**: ユーザー向けの表示はJST (Asia/Tokyo) に変換
- **スケジュール**: Celery BeatはUTCで動作し、JST時刻の設定はUTCに変換して保存

### 実装手順

#### 1. Celery設定の更新
```python
# app/core/celery_app.py に追加
celery_app.conf.update(
    timezone='UTC',
    enable_utc=True,
)
```

#### 2. アプリケーション設定の追加
```python
# app/core/config.py に追加
TIMEZONE: str = "Asia/Tokyo"  # 表示用タイムゾーン
USE_TZ: bool = True  # タイムゾーン対応を有効化
```

#### 3. Docker環境変数の設定
```yaml
# docker-compose.yml の各サービスに追加
environment:
  - TZ=Asia/Tokyo  # コンテナのシステム時刻をJSTに
```

#### 4. スケジュールサービスの更新
- JST時刻をUTCに変換してCelery Beatに登録
- データベースにはJST時刻を保存（ユーザー入力値として）

#### 5. 時刻表示の統一
- すべての時刻表示でUTC→JST変換を適用
- テンプレートフィルタを活用

## 移行時の注意点

1. 既存のスケジュールデータの移行が必要
2. ログのタイムスタンプ表示の確認
3. APIレスポンスの時刻フォーマット確認

## テスト項目

1. スケジュール登録・実行の動作確認
2. データベースへの時刻保存確認
3. UI表示の時刻確認
4. ログ出力の時刻確認