from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Optimized for Supabase Transaction Mode (Transactional Pooler)
# Using ssl="require" is the most compatible way for Supabase + asyncpg
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=10,
    pool_recycle=300,
    pool_pre_ping=True,
    connect_args={
        "prepared_statement_cache_size": 0,  # Required for PgBouncer
        "statement_cache_size": 0,
        "ssl": "require"                     # Simplified SSL for better compatibility
    }
)

async_session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db():
    async with async_session_maker() as session:
        yield session
