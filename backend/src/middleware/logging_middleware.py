"""Logging middleware with request ID tracking and comprehensive error logging."""
import logging
import sys
import time
import uuid
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive request/response logging with request ID tracking."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with logging and error tracking."""
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Log incoming request
        start_time = time.time()
        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "client_host": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            },
        )

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log response
            logger.info(
                "Request completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000, 2),
                },
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as exc:
            # Calculate duration
            duration = time.time() - start_time

            # Log error with full context
            logger.error(
                "Request failed with exception",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "duration_ms": round(duration * 1000, 2),
                    "exception_type": type(exc).__name__,
                    "exception_message": str(exc),
                },
                exc_info=True,
            )

            # Re-raise to let FastAPI's exception handlers deal with it
            raise


def get_request_id(request: Request) -> str:
    """Extract request ID from request state."""
    return getattr(request.state, "request_id", "unknown")


def log_service_error(
    request_id: str,
    service_name: str,
    operation: str,
    error: Exception,
    context: dict | None = None,
) -> None:
    """Log service layer errors with context.
    
    Args:
        request_id: Request ID for tracing
        service_name: Name of the service (e.g., 'PlanService', 'UserService')
        operation: Operation being performed (e.g., 'create_plan', 'update_user')
        error: Exception that occurred
        context: Additional context information (e.g., user_id, plan_id)
    """
    log_context = {
        "request_id": request_id,
        "service": service_name,
        "operation": operation,
        "exception_type": type(error).__name__,
        "exception_message": str(error),
    }
    
    if context:
        log_context.update(context)
    
    logger.error(
        f"Service error in {service_name}.{operation}",
        extra=log_context,
        exc_info=True,
    )


def log_database_error(
    request_id: str,
    query_description: str,
    error: Exception,
    context: dict | None = None,
) -> None:
    """Log database errors with query context.
    
    Args:
        request_id: Request ID for tracing
        query_description: Description of the query (e.g., 'fetch_user_by_email')
        error: Exception that occurred
        context: Additional context (e.g., parameters, table name)
    """
    log_context = {
        "request_id": request_id,
        "query": query_description,
        "exception_type": type(error).__name__,
        "exception_message": str(error),
    }
    
    if context:
        log_context.update(context)
    
    logger.error(
        f"Database error: {query_description}",
        extra=log_context,
        exc_info=True,
    )


def log_external_api_error(
    request_id: str,
    api_name: str,
    endpoint: str,
    error: Exception,
    context: dict | None = None,
) -> None:
    """Log external API call errors.
    
    Args:
        request_id: Request ID for tracing
        api_name: Name of external API (e.g., 'OpenAI', 'USDA')
        endpoint: API endpoint called
        error: Exception that occurred
        context: Additional context (e.g., request parameters, response status)
    """
    log_context = {
        "request_id": request_id,
        "external_api": api_name,
        "endpoint": endpoint,
        "exception_type": type(error).__name__,
        "exception_message": str(error),
    }
    
    if context:
        log_context.update(context)
    
    logger.error(
        f"External API error: {api_name} - {endpoint}",
        extra=log_context,
        exc_info=True,
    )


def log_worker_error(
    task_name: str,
    error: Exception,
    context: dict | None = None,
) -> None:
    """Log Celery worker task errors.
    
    Args:
        task_name: Name of the Celery task
        error: Exception that occurred
        context: Additional context (e.g., task arguments, user_id)
    """
    log_context = {
        "task": task_name,
        "exception_type": type(error).__name__,
        "exception_message": str(error),
    }
    
    if context:
        log_context.update(context)
    
    logger.error(
        f"Worker task error: {task_name}",
        extra=log_context,
        exc_info=True,
    )
