import os
import sys
import asyncio
import logging
from sqlalchemy import text

# 1. Add project root to sys.path first
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

# 2. Force change working directory to project root so .env is found
os.chdir(PROJECT_ROOT)

from app.infrastructure.database import engine
from app.models.base import Base

# Import all models to ensure they are registered with Base
from app.models.user import User
from app.models.chat_room import ChatRoom
from app.models.chat_member import ChatMember
from app.models.message import Message
from app.models.message_read import MessageRead
from app.models.user_block import UserBlock
from app.models.user_session import UserSession

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def cleanup_db():
    """
    Cleans up all data from all tables in the database.
    This uses TRUNCATE with CASCADE to handle foreign key constraints.
    """
    logger.info("Starting database cleanup...")
    
    # Get all table names registered in Base
    tables = Base.metadata.tables.keys()
    
    if not tables:
        logger.warning("No tables found in metadata.")
        return

    async with engine.begin() as conn:
        # Construct the TRUNCATE command for PostgreSQL
        # Truncate all tables at once to handle foreign keys efficiently
        table_names = ", ".join(f'"{table}"' for table in tables)
        truncate_query = f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE;"
        
        try:
            logger.info(f"Executing: {truncate_query}")
            await conn.execute(text(truncate_query))
            logger.info("✅ All tables cleaned successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to cleanup database: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(cleanup_db())
