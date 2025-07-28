"""Reset alembic_version table."""
import asyncio
import sys
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from app.infrastructure.database.connection import get_session


async def reset_alembic_version():
    """Reset alembic_version table."""
    async for session in get_session():
        try:
            # Check if alembic_version table exists
            result = await session.execute(
                text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'alembic_version'
                    );
                """)
            )
            exists = result.scalar()
            
            if exists:
                # Delete all records from alembic_version
                await session.execute(text("DELETE FROM alembic_version;"))
                await session.commit()
                print("Successfully cleared alembic_version table")
            else:
                print("alembic_version table does not exist")
                
        except Exception as e:
            print(f"Error: {e}")
            await session.rollback()
        finally:
            return


if __name__ == "__main__":
    asyncio.run(reset_alembic_version())