#!/usr/bin/env python
"""Celery に登録されているタスク一覧を表示するスクリプト"""
import sys
from pathlib import Path

# プロジェクトのルートディレクトリを Python パスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.infrastructure.celery.app import celery_app


def list_all_tasks():
    """Celery タスク一覧を表示"""
    print("=" * 80)
    print("Celery タスク一覧")
    print("=" * 80)
    print()
    
    # タスクを取得してソート
    tasks = sorted(celery_app.tasks.keys())
    
    # カテゴリ別に分類
    system_tasks = []
    custom_tasks = []
    
    for task_name in tasks:
        if task_name.startswith('celery.'):
            system_tasks.append(task_name)
        else:
            custom_tasks.append(task_name)
    
    # カスタムタスクを表示
    print("カスタムタスク:")
    print("-" * 40)
    if custom_tasks:
        for task in custom_tasks:
            task_obj = celery_app.tasks[task]
            print(f"  {task}")
            print(f"    - クラス: {task_obj.__class__.__name__}")
            print(f"    - モジュール: {task_obj.__module__}")
            if hasattr(task_obj, 'name'):
                print(f"    - 登録名: {task_obj.name}")
            print()
    else:
        print("  なし")
    
    # システムタスクを表示
    print("\n システムタスク (Celery 組み込み):")
    print("-" * 40)
    for task in system_tasks[:5]:  # 最初の 5 個だけ表示
        print(f"  {task}")
    if len(system_tasks) > 5:
        print(f"  ... 他 {len(system_tasks) - 5} 個")
    
    # 統計情報
    print("\n 統計:")
    print("-" * 40)
    print(f"  カスタムタスク数: {len(custom_tasks)}")
    print(f"  システムタスク数: {len(system_tasks)}")
    print(f"  合計タスク数: {len(tasks)}")
    
    # fetch_listed_info_task の詳細確認
    print("\n 特定タスクの確認:")
    print("-" * 40)
    target_task = "fetch_listed_info_task"
    
    if target_task in celery_app.tasks:
        print(f"✅ '{target_task}' は正しく登録されています")
        
        # タスクオブジェクトの詳細
        task_obj = celery_app.tasks[target_task]
        print(f"\n 詳細情報:")
        print(f"  - name 属性: {getattr(task_obj, 'name', 'なし')}")
        print(f"  - request_stack: {getattr(task_obj, 'request_stack', 'なし')}")
        print(f"  - backend: {getattr(task_obj, 'backend', 'なし')}")
        print(f"  - autoretry_for: {getattr(task_obj, 'autoretry_for', 'なし')}")
        print(f"  - max_retries: {getattr(task_obj, 'max_retries', 'なし')}")
        
        # タスクのシグネチャを確認
        if hasattr(task_obj, '__wrapped__'):
            import inspect
            sig = inspect.signature(task_obj.__wrapped__)
            print(f"  - シグネチャ: {sig}")
    else:
        print(f"❌ '{target_task}' が見つかりません")
        
        # 類似タスクを探す
        similar = [t for t in custom_tasks if 'listed' in t.lower() or 'info' in t.lower()]
        if similar:
            print(f"\n 類似のタスク名:")
            for t in similar:
                print(f"  - {t}")


def check_task_routing():
    """タスクルーティング設定を確認"""
    print("\n\n タスクルーティング設定:")
    print("=" * 80)
    
    task_routes = celery_app.conf.get('task_routes', {})
    if task_routes:
        for task_pattern, route_config in task_routes.items():
            print(f"  {task_pattern}: {route_config}")
    else:
        print("  ルーティング設定なし（デフォルトキューを使用）")


def main():
    """メイン処理"""
    list_all_tasks()
    check_task_routing()
    
    print("\n" + "=" * 80)
    print("注意事項:")
    print("- このスクリプトは Celery アプリケーションの設定のみを表示します")
    print("- 実際のタスク実行には Celery Worker と Beat が起動している必要があります")
    print("=" * 80)


if __name__ == "__main__":
    main()