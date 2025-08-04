#!/usr/bin/env python
"""サービスの起動状態を確認するスクリプト"""
import sys
import subprocess
import requests
import redis
import asyncpg
import asyncio
from pathlib import Path

# プロジェクトのルートディレクトリを Python パスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))


def check_fastapi():
    """FastAPI サーバーの確認"""
    print("1. FastAPI サーバー:")
    try:
        response = requests.get("http://localhost:8000/", timeout=2)
        print(f"   ✅ 稼働中 (status: {response.status_code})")
        return True
    except requests.exceptions.RequestException as e:
        print(f"   ❌ 接続できません")
        print(f"   起動コマンド: uvicorn app.main:app --reload")
        return False


def check_redis():
    """Redis の確認"""
    print("\n2. Redis:")
    try:
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.ping()
        print("   ✅ 稼働中")
        return True
    except Exception as e:
        print(f"   ❌ 接続できません: {e}")
        print(f"   起動コマンド: redis-server または docker-compose up -d redis")
        return False


async def check_postgres():
    """PostgreSQL の確認"""
    print("\n3. PostgreSQL:")
    try:
        # 環境変数から接続情報を取得
        from app.core.config import get_settings
        settings = get_settings()
        
        # DATABASE_URLから接続情報を解析
        import urllib.parse
        db_url = urllib.parse.urlparse(settings.database_url)
        
        conn = await asyncpg.connect(
            host=db_url.hostname or 'localhost',
            port=db_url.port or 5432,
            user=db_url.username or 'postgres',
            password=db_url.password or 'postgres',
            database=db_url.path[1:] if db_url.path else 'stockura',
        )
        await conn.close()
        print("   ✅ 稼働中")
        return True
    except Exception as e:
        print(f"   ❌ 接続できません: {e}")
        print(f"   起動コマンド: docker-compose up -d postgres")
        return False


def check_celery_worker():
    """Celery ワーカーの確認"""
    print("\n4. Celery ワーカー:")
    try:
        # celery inspect コマンドでワーカーの状態を確認
        result = subprocess.run(
            ["celery", "-A", "app.infrastructure.celery.app", "inspect", "ping"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and "pong" in result.stdout.lower():
            print("   ✅ 稼働中")
            return True
        else:
            print("   ❌ 応答なし")
            print(f"   起動コマンド: celery -A app.infrastructure.celery.app worker --loglevel=info")
            return False
    except subprocess.TimeoutExpired:
        print("   ❌ タイムアウト")
        print(f"   起動コマンド: celery -A app.infrastructure.celery.app worker --loglevel=info")
        return False
    except FileNotFoundError:
        print("   ❌ Celery がインストールされていません")
        print(f"   インストール: pip install celery")
        return False
    except Exception as e:
        print(f"   ❌ エラー: {e}")
        return False


def check_env_vars():
    """環境変数の確認"""
    print("\n5. 環境変数:")
    try:
        from app.core.config import get_settings
        settings = get_settings()
        
        required_vars = {
            "JQUANTS_EMAIL": settings.jquants_email,
            "JQUANTS_PASSWORD": settings.jquants_password,
        }
        
        all_set = True
        for var_name, var_value in required_vars.items():
            if var_value:
                print(f"   ✅ {var_name}: 設定済み")
            else:
                print(f"   ❌ {var_name}: 未設定")
                all_set = False
                
        if not all_set:
            print("\n   .env ファイルに必要な環境変数を設定してください")
            
        return all_set
    except Exception as e:
        print(f"   ❌ 設定の読み込みエラー: {e}")
        return False


async def main():
    """メイン処理"""
    print("=" * 60)
    print("サービス起動状態チェック")
    print("=" * 60)
    
    results = {
        "FastAPI": check_fastapi(),
        "Redis": check_redis(),
        "PostgreSQL": await check_postgres(),
        "Celery": check_celery_worker(),
        "環境変数": check_env_vars(),
    }
    
    print("\n" + "=" * 60)
    print("結果サマリー:")
    print("-" * 30)
    
    all_ok = True
    for service, status in results.items():
        status_text = "✅ OK" if status else "❌ NG"
        print(f"  {service:15} : {status_text}")
        if not status:
            all_ok = False
    
    print("=" * 60)
    
    if all_ok:
        print("\n✅ すべてのサービスが正常に稼働しています")
        print("   API テストを実行できます: python scripts/test_api_listed_info_auto.py")
    else:
        print("\n⚠️  一部のサービスが起動していません")
        print("   上記のメッセージを確認して、必要なサービスを起動してください")
    
    return all_ok


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())