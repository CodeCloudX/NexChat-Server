import uvicorn
import psutil
import time
import logging
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.websocket.router import websocket_router
from app.lifecycle import lifespan
from app.core.logging import setup_logging
from app.core.middleware import setup_middlewares
from app.infrastructure.database import async_session_maker
from app.infrastructure.redis import redis_client

logger = logging.getLogger(__name__)

# 1. Setup Centralized Logging
setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# 2. Setup Middlewares
setup_middlewares(app)

# 3. Setup CORS - Fix for Development
if settings.ENV == "development":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,  # Set to False when using allow_origins=["*"]
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# 4. Include Routers
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(websocket_router)


@app.get("/", tags=["system"])
def read_root():
    return {
        "app": settings.PROJECT_NAME,
        "version": "1.0.0",
        "status": "online",
        "docs": f"{settings.API_V1_STR}/docs"
    }

@app.head("/health", tags=["system"])
@app.get("/health", tags=["system"])
async def health_check():
    """
    Returns real-time server health and speed metrics.
    """
    # Check DB Latency
    start_db = time.time()
    db_status = "online"
    try:
        async with async_session_maker() as db:
            await db.execute(text("SELECT 1"))
        db_latency = round((time.time() - start_db) * 1000, 2)
    except Exception:
        db_status = "offline"
        db_latency = -1

    # Check Redis Status
    redis_status = "online" if redis_client.redis else "offline"

    def get_system_metrics():
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        return cpu, mem

    cpu_usage, memory = await run_in_threadpool(get_system_metrics)
    
    return {
        "status": "healthy" if db_status == "online" and redis_status == "online" else "degraded",
        "environment": settings.ENV,
        "speed_metrics": {
            "database_latency_ms": db_latency,
            "status": {
                "database": db_status,
                "redis": redis_status
            }
        },
        "load_metrics": {
            "cpu_usage_percent": cpu_usage,
            "memory_usage_percent": memory.percent,
            "memory_available_mb": round(memory.available / (1024 * 1024), 2),
            "memory_total_mb": round(memory.total / (1024 * 1024), 2)
        }
    }


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=(settings.ENV == "development"))
