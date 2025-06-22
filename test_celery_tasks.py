#!/usr/bin/env python3
"""
Celeryタスクのテストスクリプト
Docker環境でCeleryタスクをテストするためのサンプルコード
"""

import time
from app.tasks.sample_tasks import (
    simple_task, heavy_task, task_with_retry, 
    task_with_error_handling, chained_task, periodic_task
)
from app.tasks.stock_tasks import (
    fetch_stock_data, fetch_multiple_stocks, 
    fetch_stock_data_with_retry, analyze_stock_data
)

def test_simple_task():
    """シンプルなタスクのテスト"""
    print("=== シンプルなタスクのテスト ===")
    
    # タスクを実行
    result = simple_task.delay("Hello Celery!")
    
    # 結果を取得
    task_result = result.get(timeout=10)
    print(f"結果: {task_result}")
    print(f"タスクID: {result.id}")
    print(f"タスク状態: {result.status}")
    print()

def test_heavy_task():
    """重いタスクのテスト（進捗表示付き）"""
    print("=== 重いタスクのテスト ===")
    
    # タスクを実行（3秒間）
    result = heavy_task.delay(3)
    
    # 進捗を監視
    while not result.ready():
        if result.state == "PROGRESS":
            meta = result.info
            print(f"進捗: {meta.get('progress', 0):.1f}% - {meta.get('message', '')}")
        time.sleep(0.5)
    
    # 最終結果を取得
    task_result = result.get()
    print(f"最終結果: {task_result}")
    print()

def test_task_with_retry():
    """リトライ機能付きタスクのテスト"""
    print("=== リトライ機能付きタスクのテスト ===")
    
    # 高確率で失敗するタスクを実行
    result = task_with_retry.delay(0.8)  # 80%の確率で失敗
    
    try:
        task_result = result.get(timeout=30)
        print(f"結果: {task_result}")
    except Exception as e:
        print(f"最終的に失敗: {e}")
    
    print(f"タスク状態: {result.status}")
    print()

def test_task_with_error_handling():
    """エラーハンドリング付きタスクのテスト"""
    print("=== エラーハンドリング付きタスクのテスト ===")
    
    # 成功するタスク
    result1 = task_with_error_handling.delay("success")
    print(f"成功タスク結果: {result1.get()}")
    
    # エラーが発生するタスク
    result2 = task_with_error_handling.delay("divide_by_zero")
    print(f"エラータスク結果: {result2.get()}")
    print()

def test_chained_task():
    """チェーンタスクのテスト"""
    print("=== チェーンタスクのテスト ===")
    
    result = chained_task.delay(10)
    task_result = result.get(timeout=30)
    print(f"チェーンタスク結果: {task_result}")
    
    # 子タスクの結果を確認
    if task_result.get("status") == "tasks_launched":
        task1_id = task_result["task1_id"]
        task2_id = task_result["task2_id"]
        
        # 子タスクの結果を取得
        from app.core.celery_app import celery_app
        task1_result = celery_app.AsyncResult(task1_id)
        task2_result = celery_app.AsyncResult(task2_id)
        
        print(f"子タスク1結果: {task1_result.get()}")
        print(f"子タスク2結果: {task2_result.get()}")
        print(f"最終計算結果: {task_result['final_result']}")
    print()

def test_stock_tasks():
    """株価データ取得タスクのテスト"""
    print("=== 株価データ取得タスクのテスト ===")
    
    # 単一銘柄のデータ取得
    print("1. 単一銘柄のデータ取得")
    result = fetch_stock_data.delay("AAPL", "5d")
    
    # 進捗を監視
    while not result.ready():
        if result.state == "PROGRESS":
            meta = result.info
            print(f"進捗: {meta.get('message', '')}")
        time.sleep(1)
    
    stock_data = result.get()
    if stock_data.get("status") == "success":
        print(f"取得データ数: {len(stock_data['data'])}")
        print(f"最新価格: {stock_data['data'][-1]['close']}")
    else:
        print(f"エラー: {stock_data.get('error')}")
    print()
    
    # 複数銘柄のデータ取得
    print("2. 複数銘柄のデータ取得")
    symbols = ["AAPL", "GOOGL", "MSFT"]
    result = fetch_multiple_stocks.delay(symbols, "1d")
    
    # 進捗を監視
    while not result.ready():
        if result.state == "PROGRESS":
            meta = result.info
            print(f"進捗: {meta.get('current', 0)}/{meta.get('total', 0)} - {meta.get('message', '')}")
        time.sleep(1)
    
    multi_result = result.get()
    print(f"処理完了: {multi_result['total_symbols']}銘柄")
    for symbol, data in multi_result['results'].items():
        if data.get("status") == "success":
            print(f"  {symbol}: {len(data['data'])}件のデータ")
        else:
            print(f"  {symbol}: エラー - {data.get('error')}")
    print()
    
    # 株価分析
    print("3. 株価分析")
    result = analyze_stock_data.delay("AAPL", "1mo")
    analysis = result.get()
    
    if analysis.get("status") == "success":
        analysis_data = analysis["analysis"]
        print(f"現在価格: ${analysis_data['current_price']:.2f}")
        print(f"価格変動: {analysis_data['price_change_percent']:.2f}%")
        print(f"最高価格: ${analysis_data['highest_price']:.2f}")
        print(f"最低価格: ${analysis_data['lowest_price']:.2f}")
        print(f"ボラティリティ: {analysis_data['volatility']:.2f}%")
    else:
        print(f"分析エラー: {analysis.get('error')}")
    print()

def main():
    """メイン関数"""
    print("Celeryタスクテストを開始します...")
    print("=" * 50)
    
    try:
        # 基本的なタスクのテスト
        test_simple_task()
        test_heavy_task()
        test_task_with_retry()
        test_task_with_error_handling()
        test_chained_task()
        
        # 株価データ取得タスクのテスト
        test_stock_tasks()
        
        print("すべてのテストが完了しました！")
        
    except Exception as e:
        print(f"テスト中にエラーが発生しました: {e}")

if __name__ == "__main__":
    main() 