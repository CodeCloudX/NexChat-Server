import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from app.infrastructure.redis import redis_client
from app.utils import constants

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Performance-friendly Rate Limiting using Redis.
    Optimized to minimize Upstash commands and fix TTL reset issue.
    """
    async def dispatch(self, request: Request, call_next):
        # 1. Skip non-API routes
        if not request.url.path.startswith("/api/v1"):
            return await call_next(request)

        client_ip = request.client.host
        path = request.url.path
        limit = constants.RATE_LIMIT_DEFAULT
        
        if "/auth/" in path:
            limit = constants.RATE_LIMIT_AUTH
        elif "/messages" in path:
            limit = constants.RATE_LIMIT_MESSAGES

        rate_key = f"rate_limit:{client_ip}:{path}"
        
        if redis_client.redis:
            try:
                # Optimized: Get current count
                current_count = await redis_client.redis.get(rate_key)
                
                if current_count and int(current_count) >= limit:
                    return Response(
                        content='{"detail": "Too many requests. Please try again later."}', 
                        status_code=429,
                        media_type="application/json"
                    )
                
                # Fixed Window Logic: Increment and set TTL only if it's a new key
                async with redis_client.redis.pipeline(transaction=True) as pipe:
                    await pipe.incr(rate_key)
                    # Get TTL to see if we need to set it
                    ttl = await redis_client.redis.ttl(rate_key)
                    if ttl < 0:
                        await pipe.expire(rate_key, 60)
                    await pipe.execute()
                    
            except Exception as e:
                logger.error(f"Rate limit check failed: {e}")

        return await call_next(request)

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Performance tracking middleware.
    Adds X-Process-Time header to all responses.
    """
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        # Formatting to 4 decimal places for precision
        response.headers["X-Process-Time"] = f"{process_time:.4f}s"
        return response

def setup_middlewares(app):
    """
    Initializes custom middlewares.
    """
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RateLimitMiddleware)
