# ディレクトリ構造・ファイル名整合性改善提案書

## 概要

本ドキュメントは、 Stockura プロジェクトのディレクトリ構造とファイル名の整合性についての調査結果と改善提案をまとめたものです。

## 発見された問題点

### 1. DTO ディレクトリの命名不整合

**問題点:**
- `app/application/dto` と `app/application/dtos` が混在している
- `schedule_dto.py` のみが `dto` ディレクトリに配置され、他の DTO ファイルは `dtos` ディレクトリに存在

**影響:**
- インポート時の混乱
- 新規開発時にどちらを使用すべきか不明確

### 2. 空のディレクトリの存在

**問題点:**
以下のディレクトリが空の状態で存在している：
- `app/services/`
- `app/models/`
- `app/db/`
- `app/api/` （v1 サブディレクトリは存在）

**影響:**
- プロジェクト構造の理解を困難にする
- 新規開発者の混乱を招く

### 3. リポジトリ実装の配置不整合

**問題点:**
リポジトリ実装が複数の場所に分散している：
- `app/infrastructure/database/repositories/` - listed_info_repository_impl.py
- `app/infrastructure/repositories/` - その他のリポジトリ実装
- `app/infrastructure/redis/` - auth_repository_impl.py
- `app/infrastructure/jquants/` - auth_repository_impl.py

**影響:**
- 同じ種類のコンポーネントが異なる場所に配置されており、保守性が低下
- 新規リポジトリ追加時の配置場所が不明確

### 4. Celery タスクファイルの重複

**問題点:**
同じ機能に対して複数のバリエーションのタスクファイルが存在：
- listed_info_task.py
- listed_info_task_wrapped.py
- listed_info_task_asyncpg.py
- listed_info_task_sync.py

**影響:**
- どのファイルが実際に使用されているか不明確
- 保守時の修正漏れリスク

### 5. API エンドポイントの配置不整合

**問題点:**
- `app/api/v1/endpoints/` が空で存在
- 実際のエンドポイントは `app/presentation/api/v1/endpoints/` に配置

**影響:**
- クリーンアーキテクチャの層構造が不明確
- 重複したディレクトリ構造

### 6. モデルファイルの配置不整合

**問題点:**
- データベースモデルが `app/infrastructure/database/models/` に配置
- `listed_info_model.py` という命名（他は `_model` サフィックスなし）

**影響:**
- 命名規則の不統一
- 検索・参照時の混乱

## 改善提案

### 1. DTO ディレクトリの統一 ✅ (対応済み: 2025-08-06)

```bash
# 変更前
app/application/dto/schedule_dto.py
app/application/dtos/*.py

# 変更後
app/application/dtos/
├── __init__.py
├── schedule_dto.py
├── listed_info_dto.py
├── announcement_dto.py
├── trades_spec_dto.py
└── weekly_margin_interest_dto.py
```

**対応内容:**
- `app/application/dto/` を `app/application/dtos/` に統合
- すべての DTO ファイルを一箇所に集約

**実施済み内容:**
- `schedule_dto.py` を `dto/` から `dtos/` へ移動
- 空になった `dto/` ディレクトリを削除
- 6 つのファイルでインポート文を更新
- テストが全て成功することを確認

### 2. 空ディレクトリの削除 🔄 (TODO: 後日対応)

以下のディレクトリを削除：
- `app/services/`
- `app/models/`
- `app/db/`
- `app/api/`

**対応状況:**
- 2025-01-06: 一旦先送りとし、他の優先度の高いタスクを先に対応することに決定
- 今後の開発で必要に応じて削除を検討

### 3. リポジトリ実装の配置統一 ✅ (対応済み: 2025-01-06)

```bash
# 変更後の構造
app/infrastructure/repositories/
├── database/
│   ├── listed_info_repository_impl.py
│   ├── trades_spec_repository_impl.py
│   ├── weekly_margin_interest_repository_impl.py
│   ├── announcement_repository_impl.py
│   ├── task_log_repository.py
│   └── schedule_repository.py
├── redis/
│   └── auth_repository_impl.py
└── external/
    └── jquants_auth_repository_impl.py
```

**対応内容:**
- すべてのリポジトリ実装を `app/infrastructure/repositories/` 配下に集約
- データソース別にサブディレクトリで整理

**実施済み内容:**
- 8 つのリポジトリファイルを新しい構造に移動
- 25 以上のファイルでインポート文を更新
- テストが全て成功することを確認

### 4. Celery タスクファイルの整理 🔄 (TODO: 後日対応)

```bash
# 変更後の構造（予定）
app/infrastructure/celery/tasks/
├── __init__.py
├── listed_info_task.py      # メインタスク実装
├── trades_spec_task.py      
├── announcement_task.py     
└── weekly_margin_interest_task.py
```

**対応内容:**
- 使用されていないバリエーションファイルを削除
- 各機能につき 1 つのタスクファイルに統一
- 非同期処理の実装は内部で管理

**対応状況:**
- 2025-01-06: 調査の結果、複数のタスク名が混在しており、影響範囲が大きいため先送り
- 現在は `fetch_listed_info_task` と `fetch_listed_info_task_asyncpg` が共存
- 今後、タスク名の統一と併せて整理を検討

### 5. データベースモデル命名規則の統一 ✅ (対応済み: 2025-01-06)

```bash
# 変更前
listed_info_model.py

# 変更後
listed_info.py
```

**対応内容:**
- `_model` サフィックスを削除し、他のモデルファイルと統一

**実施済み内容:**
- `listed_info_model.py` を `listed_info.py` にリネーム
- 4 つのファイルでインポート文を更新
- テストが全て成功することを確認

### 6. クリーンアーキテクチャ準拠の強化

**現在の問題点:**
- `app/presentation/` 層が `app/infrastructure/` の具体的な実装に依存している箇所がある
- ドメイン層とインフラストラクチャ層の境界が曖昧

**改善案:**
- 依存性注入の徹底
- インターフェースと実装の明確な分離
- 各層の責務の明確化

## 実装優先順位

1. **高優先度（即時対応推奨）**
   - DTO ディレクトリの統一 ✅ (完了)
   - 空ディレクトリの削除 🔄 (TODO: 後日対応)
   - Celery タスクファイルの整理 🔄 (TODO: 後日対応)

2. **中優先度（段階的対応）**
   - リポジトリ実装の配置統一 ✅ (完了)
   - データベースモデル命名規則の統一 ✅ (完了)

3. **低優先度（長期的改善）**
   - クリーンアーキテクチャ準拠の強化

## 実装時の注意事項

1. **インポート文の更新**
   - ディレクトリ構造変更に伴い、すべての関連インポート文を更新する必要がある
   - IDE の自動リファクタリング機能の活用を推奨

2. **テストの実行**
   - 各変更後は必ずテストスイートを実行し、影響がないことを確認

3. **段階的な実装**
   - 一度にすべてを変更するのではなく、機能単位で段階的に実装
   - 各段階でのテストとレビューを徹底

4. **ドキュメントの更新**
   - `docs/FILE_STRUCTURE.md` の更新
   - `docs/ARCHITECTURE.md` への変更内容の反映

## まとめ

本提案を実装することで、以下の効果が期待できます：

1. **開発効率の向上**: 統一された構造により、ファイルの検索・追加が容易に
2. **保守性の向上**: 整合性のある構造により、バグの混入リスクを低減
3. **新規開発者のオンボーディング改善**: 明確な構造により、プロジェクト理解が容易に
4. **クリーンアーキテクチャの徹底**: 各層の責務が明確になり、変更に強い設計を実現

これらの改善により、 Stockura プロジェクトの長期的な保守性と拡張性が大幅に向上することが期待されます。