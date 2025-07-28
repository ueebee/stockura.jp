# v2 移行済み旧モジュール削除の実装計画

## 実装ステップ

### ステップ 1: 事前確認（5 分）
1. 現在のブランチ確認
   ```bash
   git status
   ```

2. テストの実行（削除前の状態確認）
   ```bash
   pytest tests/
   ```

3. アプリケーションの起動確認
   ```bash
   python app/main.py
   ```

### ステップ 2: ファイル削除（3 分）
1. 旧エンティティファイルの削除
   ```bash
   rm app/domain/entities/stock_old.py
   rm app/domain/entities/price_old.py
   ```

2. カバレッジレポートファイルの削除
   ```bash
   rm htmlcov/z_3efee37c27925ae3_stock_old_py.html
   rm htmlcov/z_3efee37c27925ae3_price_old_py.html
   ```

### ステップ 3: 動作確認（5 分）
1. import エラーチェック
   ```bash
   python -m py_compile app/**/*.py
   ```

2. テストの再実行
   ```bash
   pytest tests/
   ```

3. アプリケーションの起動確認
   ```bash
   python app/main.py
   ```

### ステップ 4: コミット（3 分）
1. 変更の確認
   ```bash
   git status
   git diff
   ```

2. コミット
   ```bash
   git add -A
   git commit -m "feat: v2 移行済みの旧モジュール (stock_old.py, price_old.py) を削除"
   ```

## タイムライン
- 総所要時間: 約 16 分
- 各ステップは独立しており、問題があれば即座に停止可能

## チェックリスト
- [ ] git status でクリーンな状態から開始
- [ ] 削除前のテストがすべてパス
- [ ] ファイル削除実行
- [ ] 削除後のテストがすべてパス
- [ ] import エラーなし
- [ ] アプリケーション起動確認
- [ ] 適切なコミットメッセージ

## 緊急時の対応
問題が発生した場合：
```bash
# ファイルの復元
git checkout HEAD -- app/domain/entities/stock_old.py
git checkout HEAD -- app/domain/entities/price_old.py

# または全体のリセット
git reset --hard HEAD
```

## 実装後の確認事項
- `app/domain/entities/`ディレクトリに旧ファイルが存在しないこと
- すべてのテストが正常に動作すること
- アプリケーションが正常に起動すること