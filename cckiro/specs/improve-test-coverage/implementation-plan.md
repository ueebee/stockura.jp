# テストカバレッジ向上 実装計画書

## 1. 実装計画概要
本計画書は、テストカバレッジを 41.60% から 80% 以上に向上させるための具体的な実装手順を定義します。
3 つのフェーズに分けて段階的に実装を進めていきます。

## 2. 実装タイムライン

### Phase 1: コアビジネスロジックのテスト（目標: 55% 達成）
**期間**: 3-4 日
**対象モジュール**:
- `analyze_stock.py` (92 行)
- `fetch_stock_price.py` (57 行)
- `stock_repository_impl.py` (JQuants 版) (94 行)

### Phase 2: DTO ・インターフェース・サービス層（目標: 70% 達成）
**期間**: 2-3 日
**対象モジュール**:
- `stock_dto.py` (97 行)
- 外部 API インターフェース (82 行)
- `price_calculator.py` (92 行)

### Phase 3: その他のモジュール（目標: 80% 達成）
**期間**: 2 日
**対象モジュール**:
- データベース関連
- Value Objects
- 例外クラス

## 3. Phase 1 実装詳細

### 3.1 事前準備タスク
```bash
# 1. テストディレクトリの作成
mkdir -p tests/unit/application/use_cases
mkdir -p tests/mocks
mkdir -p tests/factories

# 2. 必要なテストユーティリティの作成
- tests/mocks/jquants_mock.py
- tests/factories/price_factory.py
- conftest.py の拡張
```

### 3.2 analyze_stock.py テスト実装
**ファイル**: `tests/unit/application/use_cases/test_analyze_stock.py`

**実装順序**:
1. モックとフィクスチャのセットアップ
2. 正常系テストケース（5 件）
   - 有効な銘柄コードでの分析
   - カスタム期間での分析
   - 買い・売り・保有推奨の生成
3. 異常系テストケース（4 件）
   - 無効な銘柄コード
   - 価格データなし
   - API エラー
4. エッジケース（2 件）
   - 極端なボラティリティ
   - 出来高ゼロ

**推定作業時間**: 4-5 時間

### 3.3 fetch_stock_price.py テスト実装
**ファイル**: `tests/unit/application/use_cases/test_fetch_stock_price.py`

**実装順序**:
1. 価格データのモック作成
2. 正常系テストケース（4 件）
   - 最新価格の取得
   - 特定日付の価格取得
   - キャッシュヒット/ミス
3. 異常系テストケース（4 件）
   - 無効な銘柄コード
   - 未来日付、週末日付
   - API エラー
4. データソース切り替えテスト（2 件）

**推定作業時間**: 3-4 時間

### 3.4 JQuants Stock Repository テスト実装
**ファイル**: `tests/unit/infrastructure/jquants/test_stock_repository_impl.py`

**実装順序**:
1. JQuants API レスポンスのモック作成
2. 基本機能テスト（4 件）
   - 上場銘柄一覧取得
   - 銘柄コードでの検索
   - 銘柄名での検索
3. キャッシュ機能テスト（3 件）
4. エラーハンドリング（3 件）

**推定作業時間**: 4-5 時間

## 4. 実装時の注意事項

### 4.1 コーディング規約
- Black でのフォーマット統一
- 型ヒントの使用
- docstring の記載
- テストメソッド名は`test_`で開始

### 4.2 モックの使用方針
- 外部 API コールは必ずモック化
- データベースアクセスはインメモリ DB またはモック
- 日時は`freezegun`で固定
- ランダム値は`faker`で生成

### 4.3 アサーションのベストプラクティス
```python
# Good
assert result.code == "1234"
assert result.recommendation == "BUY"
assert len(result.prices) == 30

# Better (詳細なエラーメッセージ)
assert result.code == "1234", f"Expected code 1234, got {result.code}"
assert result.recommendation == "BUY", f"Expected BUY recommendation, got {result.recommendation}"
```

## 5. カバレッジ測定と確認

### 5.1 ローカルでの確認方法
```bash
# Phase 1 完了後の確認
pytest tests/unit/application/use_cases/test_analyze_stock.py --cov=app.application.use_cases.analyze_stock --cov-report=term-missing

# 全体カバレッジの確認
pytest --cov=app --cov-report=html
# htmlcov/index.html をブラウザで開く
```

### 5.2 目標達成の確認ポイント
- Phase 1 後: 全体カバレッジ 55% 以上
- 対象モジュールのカバレッジ 90% 以上
- 新規テストがすべてパス

## 6. トラブルシューティング

### 6.1 よくある問題と対処法
1. **インポートエラー**
   ```bash
   # PYTHONPATH の設定
   export PYTHONPATH="${PYTHONPATH}:${PWD}"
   ```

2. **非同期テストの問題**
   ```python
   # pytest-asyncio の使用
   @pytest.mark.asyncio
   async def test_async_method():
       result = await some_async_method()
   ```

3. **モックが効かない**
   - モックのパスが正しいか確認
   - インポートのタイミングを確認

## 7. Phase 2 以降の準備

### 7.1 Phase 2 で必要な準備
- DTO のテストデータ構造設計
- 外部 API レスポンスの実データ収集
- 価格計算ロジックの仕様確認

### 7.2 Phase 3 で必要な準備
- データベーススキーマの理解
- Value Objects の振る舞い確認
- 例外処理フローの整理

## 8. コミットと PR 戦略

### 8.1 コミット単位
- 1 つのテストファイル = 1 コミット
- コミットメッセージ例:
  ```
  test: add unit tests for analyze_stock use case
  
  - Add tests for normal cases (5 tests)
  - Add tests for error cases (4 tests)
  - Add edge case tests (2 tests)
  - Coverage: 92% for analyze_stock.py
  ```

### 8.2 PR 作成
- Phase 完了ごとに PR 作成
- カバレッジレポートを PR に含める
- レビュー観点:
  - テストの網羅性
  - モックの適切性
  - 実行時間

## 9. 成功の定義

### 9.1 Phase 1 成功基準
- [ ] analyze_stock.py のカバレッジ 90% 以上
- [ ] fetch_stock_price.py のカバレッジ 90% 以上
- [ ] stock_repository_impl.py のカバレッジ 85% 以上
- [ ] 全体カバレッジ 55% 以上
- [ ] すべてのテストが 2 秒以内に完了

### 9.2 最終成功基準
- [ ] 全体カバレッジ 80% 以上
- [ ] CI/CD での自動実行設定完了
- [ ] ドキュメント更新完了