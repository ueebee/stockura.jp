import time
import random
from celery import current_task
from app.core.celery_app import celery_app

@celery_app.task(bind=True)
def simple_task(self, message: str) -> str:
    """シンプルなタスクの例"""
    print(f"Simple task started: {message}")
    return f"Task completed: {message}"

@celery_app.task(bind=True)
def heavy_task(self, duration: int = 5) -> dict:
    """重い処理をシミュレートするタスク"""
    print(f"Heavy task started, duration: {duration} seconds")
    
    # 進捗を更新
    for i in range(duration):
        time.sleep(1)
        progress = (i + 1) / duration * 100
        self.update_state(
            state="PROGRESS",
            meta={"current": i + 1, "total": duration, "progress": progress}
        )
        print(f"Progress: {progress:.1f}%")
    
    result = {
        "status": "completed",
        "duration": duration,
        "message": f"Heavy task completed in {duration} seconds"
    }
    
    print(f"Heavy task completed: {result}")
    return result

@celery_app.task(bind=True, max_retries=3)
def task_with_retry(self, fail_probability: float = 0.3) -> str:
    """リトライ機能付きタスクの例"""
    print(f"Task with retry started, fail probability: {fail_probability}")
    
    # ランダムに失敗をシミュレート
    if random.random() < fail_probability:
        print("Task failed, retrying...")
        raise self.retry(countdown=5, exc=Exception("Random failure"))
    
    return "Task with retry completed successfully"

@celery_app.task(bind=True)
def task_with_error_handling(self, operation: str) -> dict:
    """エラーハンドリング付きタスクの例"""
    print(f"Task with error handling started: {operation}")
    
    try:
        if operation == "divide_by_zero":
            result = 1 / 0
        elif operation == "index_error":
            result = [1, 2, 3][10]
        elif operation == "success":
            result = "Operation completed successfully"
        else:
            result = f"Unknown operation: {operation}"
        
        return {
            "status": "success",
            "result": result,
            "operation": operation
        }
        
    except Exception as e:
        print(f"Error in task: {e}")
        return {
            "status": "error",
            "error": str(e),
            "operation": operation
        }

@celery_app.task(bind=True)
def chained_task(self, value: int) -> dict:
    """チェーンタスクの例（他のタスクを呼び出す）"""
    print(f"Chained task started with value: {value}")
    
    # 他のタスクを非同期的に呼び出す
    result1 = simple_task.delay(f"First step with {value}")
    result2 = simple_task.delay(f"Second step with {value}")
    
    # タスクIDを返す（結果は後で取得）
    return {
        "status": "tasks_launched",
        "value": value,
        "task1_id": result1.id,
        "task2_id": result2.id,
        "final_result": value * 2
    }

@celery_app.task(bind=True)
def periodic_task(self) -> str:
    """定期的に実行されるタスクの例"""
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"Periodic task executed at: {current_time}")
    
    return f"Periodic task completed at {current_time}" 