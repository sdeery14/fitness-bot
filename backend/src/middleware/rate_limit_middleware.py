"""Rate limiting middleware using Redis for distributed rate limiting."""
import time
from collections.abc import Callable

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from src.utils.cache import get_redis_client


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting API requests.

    Rate limits:
    - Auth endpoints (/api/v1/auth/*): 5 requests per minute
    - General endpoints: 100 requests per minute
    """

    # Rate limit configurations (requests per minute)
    AUTH_RATE_LIMIT = 5
    GENERAL_RATE_LIMIT = 100

    # Exempted paths (no rate limiting)
    EXEMPTED_PATHS = [
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health",
    ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""
        # Skip rate limiting for exempted paths
        if any(request.url.path.startswith(path) for path in self.EXEMPTED_PATHS):
            return await call_next(request)

        # Determine rate limit based on path
        if request.url.path.startswith("/api/v1/auth"):
            rate_limit = self.AUTH_RATE_LIMIT
            window_name = "auth"
        else:
            rate_limit = self.GENERAL_RATE_LIMIT
            window_name = "general"

        # Get client identifier (IP address or user ID from JWT)
        client_id = self._get_client_identifier(request)

        # Check rate limit
        try:
            allowed = await self._check_rate_limit(
                client_id=client_id,
                window_name=window_name,
                rate_limit=rate_limit,
            )

            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": f"Rate limit exceeded. Maximum {rate_limit} requests per minute allowed.",
                        }
                    },
                )

            # Process request
            response = await call_next(request)

            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(rate_limit)
            response.headers["X-RateLimit-Window"] = "60"  # seconds

            return response

        except HTTPException:
            raise
        except Exception:
            # If rate limiting fails (e.g., Redis unavailable), allow request
            # but log the error (handled by logging middleware)
            return await call_next(request)

    def _get_client_identifier(self, request: Request) -> str:
        """Get unique client identifier for rate limiting.

        Priority:
        1. User ID from JWT token (if authenticated)
        2. Client IP address
        """
        # Try to get user ID from request state (set by auth middleware)
        if hasattr(request.state, "user_id"):
            return f"user:{request.state.user_id}"

        # Fall back to IP address
        if request.client:
            return f"ip:{request.client.host}"

        return "unknown"

    async def _check_rate_limit(
        self,
        client_id: str,
        window_name: str,
        rate_limit: int,
    ) -> bool:
        """Check if client has exceeded rate limit.

        Uses sliding window counter algorithm with Redis.

        Args:
            client_id: Unique client identifier
            window_name: Rate limit window name (auth/general)
            rate_limit: Maximum requests allowed per minute

        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        redis_client = get_redis_client()
        if not redis_client:
            # If Redis is unavailable, allow request
            return True

        # Generate Redis key
        current_minute = int(time.time() / 60)
        key = f"ratelimit:{window_name}:{client_id}:{current_minute}"

        try:
            # Increment counter
            count = await redis_client.incr(key)

            # Set expiration on first request (TTL = 2 minutes for safety)
            if count == 1:
                await redis_client.expire(key, 120)

            # Check if limit exceeded
            return count <= rate_limit

        except Exception:
            # If Redis operation fails, allow request
            return True


def get_rate_limit_info(client_id: str, window_name: str) -> dict:
    """Get current rate limit status for a client.

    Args:
        client_id: Unique client identifier
        window_name: Rate limit window name (auth/general)

    Returns:
        Dictionary with limit, remaining, and reset_at information
    """
    redis_client = get_redis_client()
    if not redis_client:
        return {
            "limit": 0,
            "remaining": 0,
            "reset_at": 0,
        }

    # Determine rate limit
    if window_name == "auth":
        rate_limit = RateLimitMiddleware.AUTH_RATE_LIMIT
    else:
        rate_limit = RateLimitMiddleware.GENERAL_RATE_LIMIT

    # Get current count
    current_minute = int(time.time() / 60)
    key = f"ratelimit:{window_name}:{client_id}:{current_minute}"

    try:
        count = redis_client.get(key)
        count = int(count) if count else 0

        return {
            "limit": rate_limit,
            "remaining": max(0, rate_limit - count),
            "reset_at": (current_minute + 1) * 60,  # Next minute
        }

    except Exception:
        return {
            "limit": rate_limit,
            "remaining": rate_limit,
            "reset_at": (current_minute + 1) * 60,
        }
