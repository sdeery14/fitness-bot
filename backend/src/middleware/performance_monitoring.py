"""Performance monitoring middleware for FastAPI.

Tracks request duration, response times, and identifies slow operations.
"""
import time
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware to track API performance metrics."""

    def __init__(
        self,
        app: ASGIApp,
        slow_request_threshold: float = 1.0,  # seconds
    ) -> None:
        """Initialize performance monitoring middleware.

        Args:
            app: ASGI application
            slow_request_threshold: Log requests slower than this (seconds)
        """
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """Process request and track performance metrics.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response with performance headers
        """
        start_time = time.time()

        # Add request ID for tracing
        request_id = request.headers.get("X-Request-ID", f"req_{int(start_time * 1000)}")

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time
        duration_ms = duration * 1000

        # Add performance headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

        # Log slow requests
        if duration > self.slow_request_threshold:
            import logging
            logger = logging.getLogger("performance")
            logger.warning(
                f"Slow request detected: {request.method} {request.url.path} "
                f"took {duration_ms:.2f}ms (threshold: {self.slow_request_threshold * 1000}ms) "
                f"[Request ID: {request_id}]"
            )

        # Log metrics to stdout (for CloudWatch/aggregation)
        import os
        if os.getenv("ENVIRONMENT") == "production":
            print(
                f"METRIC request_duration={duration_ms:.2f} "
                f"method={request.method} "
                f"path={request.url.path} "
                f"status={response.status_code} "
                f"request_id={request_id}"
            )

        return response


class AIResponseTimeTracker:
    """Track AI agent response times for monitoring."""

    def __init__(self) -> None:
        """Initialize AI response time tracker."""
        self.response_times: list[float] = []

    async def track_ai_request(
        self,
        operation: str,
        agent_name: str,
        callback: Callable,
    ) -> tuple[any, float]:
        """Track an AI operation and measure response time.

        Args:
            operation: Operation name (e.g., "plan_generation", "conversation")
            agent_name: Name of the agent being called
            callback: Async function to execute

        Returns:
            Tuple of (result, duration_seconds)
        """
        import logging
        logger = logging.getLogger("ai_performance")

        start_time = time.time()

        try:
            result = await callback()
            duration = time.time() - start_time

            # Track for statistics
            self.response_times.append(duration)

            # Log AI performance
            logger.info(
                f"AI operation completed: {operation} (agent: {agent_name}) "
                f"took {duration:.2f}s"
            )

            # Log metric
            import os
            if os.getenv("ENVIRONMENT") == "production":
                print(
                    f"METRIC ai_response_time={duration:.2f} "
                    f"operation={operation} "
                    f"agent={agent_name}"
                )

            # Alert on very slow responses (>30 seconds)
            if duration > 30.0:
                logger.warning(
                    f"Very slow AI response: {operation} took {duration:.2f}s "
                    f"(agent: {agent_name})"
                )

            return result, duration

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"AI operation failed: {operation} (agent: {agent_name}) "
                f"after {duration:.2f}s - Error: {str(e)}"
            )
            raise

    def get_statistics(self) -> dict:
        """Get AI response time statistics.

        Returns:
            Dict with p50, p95, p99 response times
        """
        if not self.response_times:
            return {
                "count": 0,
                "p50": 0.0,
                "p95": 0.0,
                "p99": 0.0,
                "mean": 0.0,
            }

        import statistics

        sorted_times = sorted(self.response_times)
        count = len(sorted_times)

        return {
            "count": count,
            "p50": sorted_times[int(count * 0.50)] if count > 0 else 0.0,
            "p95": sorted_times[int(count * 0.95)] if count > 1 else sorted_times[0],
            "p99": sorted_times[int(count * 0.99)] if count > 1 else sorted_times[0],
            "mean": statistics.mean(sorted_times),
        }


class DatabaseQueryLogger:
    """Log slow database queries for optimization."""

    def __init__(self, slow_query_threshold: float = 0.1) -> None:
        """Initialize database query logger.

        Args:
            slow_query_threshold: Log queries slower than this (seconds)
        """
        self.slow_query_threshold = slow_query_threshold

    async def track_query(
        self,
        query_description: str,
        callback: Callable,
    ) -> any:
        """Track a database query and log if slow.

        Args:
            query_description: Description of the query
            callback: Async function that executes the query

        Returns:
            Query result
        """
        import logging
        logger = logging.getLogger("database_performance")

        start_time = time.time()

        try:
            result = await callback()
            duration = time.time() - start_time

            # Log slow queries
            if duration > self.slow_query_threshold:
                logger.warning(
                    f"Slow database query: {query_description} "
                    f"took {duration * 1000:.2f}ms "
                    f"(threshold: {self.slow_query_threshold * 1000}ms)"
                )

                # Log metric
                import os
                if os.getenv("ENVIRONMENT") == "production":
                    print(
                        f"METRIC slow_query_duration={duration * 1000:.2f} "
                        f"query={query_description}"
                    )

            return result

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Database query failed: {query_description} "
                f"after {duration * 1000:.2f}ms - Error: {str(e)}"
            )
            raise


# Global instances for use across the application
ai_tracker = AIResponseTimeTracker()
db_logger = DatabaseQueryLogger()
