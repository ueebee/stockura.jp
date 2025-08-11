# Presentation 層のクリーンアーキテクチャ改善 - 実装計画書（第 1 回：依存性注入の改善）

## 1. 実装概要

本実装計画書は、設計書に基づいて依存性注入の改善を段階的に実装するための詳細な手順を記述します。
各ステップで動作確認を行い、既存の機能を壊さないことを保証します。

## 2. 実装ステップ

### ステップ 1: 依存性注入の基盤整備（30 分）

#### 1.1 ディレクトリ構造の作成
```bash
# 以下のディレクトリ・ファイルを作成
app/presentation/dependencies/
├── __init__.py
├── repositories.py
├── use_cases.py
└── services.py
```

#### 1.2 repositories.py の実装
- スケジュールリポジトリの依存性注入関数を実装
- タスクログリポジトリの依存性注入関数を実装
- 認証リポジトリの依存性注入関数を実装

#### 1.3 use_cases.py の実装
- ManageScheduleUseCase の依存性注入関数を実装
- AuthUseCase の依存性注入関数を実装

#### 1.4 services.py の実装
- ScheduleEventPublisher の依存性注入関数を実装
- 既存の infrastructure/di/providers.py から移行

#### 1.5 動作確認
- インポートエラーがないことを確認
- 既存のテストが通ることを確認

### ステップ 2: schedules.py の移行（20 分）

#### 2.1 インポートの修正
- インフラストラクチャ層の具体的な実装のインポートを削除
- presentation/dependencies からのインポートに変更

#### 2.2 依存性注入の適用
- get_manage_schedule_use_case 関数を削除（dependencies モジュールのものを使用）
- 各エンドポイントで Depends() を使用した依存性注入に変更
- Celery タスクの直接インポートを削除

#### 2.3 動作確認
- API テスト（test_schedules.py）が通ることを確認
- 手動で API エンドポイントをテスト

### ステップ 3: auth.py の移行（15 分）

#### 3.1 インポートの修正
- RedisAuthRepository の直接インポートを削除
- presentation/dependencies からのインポートに変更

#### 3.2 依存性注入の適用
- get_auth_repository 関数を削除
- get_auth_use_case 関数を削除
- dependencies モジュールの関数を使用

#### 3.3 動作確認
- API テスト（test_auth.py）が通ることを確認
- 認証フローが正常に動作することを確認

### ステップ 4: listed_info_schedules.py の確認と移行（15 分）

#### 4.1 ファイルの存在確認
- listed_info_schedules.py が存在するか確認
- 存在する場合は同様の移行を実施

#### 4.2 その他のエンドポイントの確認
- presentation/api/v1/endpoints/以下の他のファイルを確認
- 依存性注入が必要な箇所を特定

### ステップ 5: 既存プロバイダーの統合（10 分）

#### 5.1 infrastructure/di/providers.py の確認
- 既存の内容を確認
- presentation/dependencies に移行済みか確認

#### 5.2 クリーンアップ
- 不要になったインポートの削除
- コメントの整理

### ステップ 6: 最終テストと確認（20 分）

#### 6.1 全体テストの実行
```bash
# 全てのテストを実行
pytest tests/

# 特に以下のテストに注目
- tests/test_api/test_schedules.py
- tests/test_api/test_auth.py
- tests/test_api/test_listed_info_schedules.py（存在する場合）
```

#### 6.2 手動テスト
- Swagger UI を使用して各エンドポイントをテスト
- 認証フローの動作確認
- スケジュールの作成・更新・削除の確認

#### 6.3 インポート分析
- プレゼンテーション層からインフラストラクチャ層への直接的な依存がないことを確認
```bash
# 依存関係の確認コマンド例
grep -r "from app.infrastructure" app/presentation/ --include="*.py" | grep -v "dependencies"
```

## 3. 実装の注意事項

### 3.1 循環インポートの回避
- 依存性注入関数内で動的インポートを使用
- インポートは関数内で行い、モジュールレベルでは行わない

### 3.2 後方互換性の維持
- API のインターフェースは変更しない
- レスポンスの形式は変更しない
- 既存のテストケースは修正しない

### 3.3 エラーハンドリング
- 依存性注入に失敗した場合の適切なエラーメッセージ
- ログ出力の確認

## 4. ロールバック計画

問題が発生した場合：
1. git stash で変更を一時保存
2. git checkout .で変更を破棄
3. 問題の原因を特定
4. 修正して再実装

## 5. 完了基準

- [ ] presentation/dependencies ディレクトリが作成されている
- [ ] 全ての依存性注入関数が実装されている
- [ ] schedules.py がインフラストラクチャ層に直接依存していない
- [ ] auth.py がインフラストラクチャ層に直接依存していない
- [ ] 全てのテストが通る
- [ ] 手動テストで正常動作を確認

## 6. 実装順序の根拠

1. **依存性注入の基盤を最初に整備**: 他の変更の前提となるため
2. **schedules.py を先に移行**: 最も複雑で影響範囲が大きいため
3. **auth.py を次に移行**: 比較的シンプルで確認しやすいため
4. **最後に統合とテスト**: 全体の動作確認と品質保証のため

---

この実装計画に問題がないか確認してください。問題がある場合は、修正すべき点を教えてください。