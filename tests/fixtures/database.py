"""
データベース関連のテストフィクスチャ

テスト用のデータベースセッション、トランザクション管理、
クリーンアップ処理などを提供します。
"""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.base import Base
from app.models import Company, DailyQuote, DataSource


@pytest_asyncio.fixture
async def clean_tables(async_session: AsyncSession):
    """
    テーブルをクリーンな状態にリセットするフィクスチャ
    
    各テストの前にすべてのテーブルのデータを削除します。
    外部キー制約を考慮した順序で削除を行います。
    """
    # 外部キー制約を考慮した削除順序
    tables_to_clean = [
        "daily_quotes",
        "companies", 
        "data_sources",
        "market_master",
        "sector17_master",
        "sector33_master"
    ]
    
    for table in tables_to_clean:
        await async_session.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
    
    await async_session.commit()
    yield
    # テスト後のクリーンアップは自動ロールバックで処理


@pytest_asyncio.fixture
async def seed_master_data(async_session: AsyncSession):
    """
    マスターデータをシードするフィクスチャ
    
    市場区分、業種分類などのマスターデータを投入します。
    """
    # 市場区分マスター
    market_data = [
        {"code": "0101", "name": "東証プライム"},
        {"code": "0102", "name": "東証スタンダード"},
        {"code": "0104", "name": "東証グロース"},
        {"code": "0106", "name": "TOKYO PRO Market"},
    ]
    
    for market in market_data:
        await async_session.execute(
            text("INSERT INTO market_master (code, name) VALUES (:code, :name) ON CONFLICT DO NOTHING"),
            market
        )
    
    # 17業種マスター（一部抜粋）
    sector17_data = [
        {"code": "1", "name": "食品"},
        {"code": "2", "name": "エネルギー資源"},
        {"code": "3", "name": "建設・資材"},
        {"code": "4", "name": "素材・化学"},
        {"code": "5", "name": "医薬品"},
    ]
    
    for sector in sector17_data:
        await async_session.execute(
            text("INSERT INTO sector17_master (code, name) VALUES (:code, :name) ON CONFLICT DO NOTHING"),
            sector
        )
    
    await async_session.commit()
    yield


@pytest.fixture
def db_queries():
    """
    よく使用するデータベースクエリを提供するフィクスチャ
    
    テストで頻繁に使用するクエリヘルパー関数を提供します。
    """
    class DBQueries:
        @staticmethod
        async def count_companies(session: AsyncSession) -> int:
            """企業数をカウント"""
            result = await session.execute(text("SELECT COUNT(*) FROM companies"))
            return result.scalar()
        
        @staticmethod
        async def count_daily_quotes(session: AsyncSession) -> int:
            """株価データ数をカウント"""
            result = await session.execute(text("SELECT COUNT(*) FROM daily_quotes"))
            return result.scalar()
        
        @staticmethod
        async def get_company_by_code(session: AsyncSession, code: str):
            """企業コードで企業を取得"""
            result = await session.execute(
                text("SELECT * FROM companies WHERE code = :code"),
                {"code": code}
            )
            return result.first()
        
        @staticmethod
        async def get_latest_quote(session: AsyncSession, code: str):
            """指定銘柄の最新株価を取得"""
            result = await session.execute(
                text("""
                    SELECT * FROM daily_quotes 
                    WHERE code = :code 
                    ORDER BY date DESC 
                    LIMIT 1
                """),
                {"code": code}
            )
            return result.first()
    
    return DBQueries()


@pytest.fixture
async def transaction_rollback(async_session: AsyncSession):
    """
    トランザクションロールバックを保証するフィクスチャ
    
    テスト中のすべての変更を自動的にロールバックします。
    ネストしたトランザクションを使用してテストの独立性を保証。
    """
    # セーブポイントを作成
    async with async_session.begin_nested() as nested:
        yield async_session
    
    # ネストしたトランザクションは自動的にロールバック
    await async_session.rollback()


@pytest_asyncio.fixture
async def db_statistics(async_session: AsyncSession):
    """
    データベース統計情報を提供するフィクスチャ
    
    テストのデバッグやアサーションで使用する統計情報を提供。
    """
    class DBStatistics:
        def __init__(self, session: AsyncSession):
            self.session = session
        
        async def get_table_stats(self):
            """各テーブルのレコード数を取得"""
            tables = ["companies", "daily_quotes", "data_sources"]
            stats = {}
            
            for table in tables:
                result = await self.session.execute(
                    text(f"SELECT COUNT(*) as count FROM {table}")
                )
                stats[table] = result.scalar()
            
            return stats
        
        async def get_date_range(self, table: str = "daily_quotes"):
            """日付範囲を取得"""
            result = await self.session.execute(
                text(f"""
                    SELECT 
                        MIN(date) as min_date,
                        MAX(date) as max_date
                    FROM {table}
                """)
            )
            row = result.first()
            return {
                "min_date": row.min_date if row else None,
                "max_date": row.max_date if row else None
            }
    
    return DBStatistics(async_session)