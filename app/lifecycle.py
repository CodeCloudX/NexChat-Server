import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import text

from app.infrastructure.redis import redis_client
from app.infrastructure.database import async_session_maker
from app.infrastructure.push import init_firebase
from app.background.tasks import cleanup_old_data_task

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup and shutdown events for the application.
    Security Note: Logs are cleaned to avoid revealing sensitive file paths.
    """
    # --- STARTUP ---
    logger.info("Starting up NexChat Backend...")
    
    # 1. DB Check
    try:
        async with async_session_maker() as db:
            await db.execute(text("SELECT 1"))
        logger.info("Database connection established.")
    except Exception:
        # Avoid logging 'e' directly as it contains file paths and credentials
        logger.error("Database connection failed. Please check your credentials and SSL settings.")

    # 2. Redis Check
    try:
        if await redis_client.connect():
            logger.info("Redis connected successfully.")
        else:
            logger.error("Redis connection failed: Authentication or endpoint error.")
    except Exception:
        logger.error("Redis connection failed due to an unexpected error.")

    # 3. Firebase Initialize
    try:
        init_firebase()
        logger.info("Firebase initialized successfully.")
    except Exception:
        logger.error("Firebase initialization failed. Ensure the credential file exists and is valid.")

    # 4. Background Tasks
    app.state.maintenance_task = asyncio.create_task(cleanup_old_data_task())
    logger.info("Background tasks started.")
    
    yield
    
    # --- SHUTDOWN ---
    logger.info("Shutting down NexChat Backend...")
    if hasattr(app.state, 'maintenance_task'):
        app.state.maintenance_task.cancel()
    
    await redis_client.disconnect()
    logger.info("Graceful shutdown complete.")
