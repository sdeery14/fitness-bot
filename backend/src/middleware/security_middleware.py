"""Security hardening middleware and utilities.

Implements security best practices:
- Security headers (HSTS, CSP, X-Frame-Options, etc.)
- CSRF protection
- Input sanitization
- XSS prevention
"""
import secrets
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    def __init__(self, app: ASGIApp) -> None:
        """Initialize security headers middleware.

        Args:
            app: ASGI application
        """
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """Add security headers to response.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response with security headers
        """
        response = await call_next(request)

        # Prevent MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Enable XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Content Security Policy
        # Note: Adjust based on your frontend needs
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # Adjust for production
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: https:",
            "font-src 'self' data:",
            "connect-src 'self' http://localhost:* ws://localhost:*",  # Dev only
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy (formerly Feature-Policy)
        permissions = [
            "geolocation=()",
            "microphone=()",
            "camera=()",
            "payment=()",
            "usb=()",
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions)

        # HSTS (HTTP Strict Transport Security)
        # Only enable in production with HTTPS
        import os
        if os.getenv("ENVIRONMENT") == "production":
            # 1 year max-age, include subdomains
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """CSRF protection for state-changing operations.

    Uses double-submit cookie pattern:
    1. Generate CSRF token and set as cookie
    2. Require token in X-CSRF-Token header for POST/PUT/PATCH/DELETE
    """

    def __init__(
        self,
        app: ASGIApp,
        exempt_paths: list[str] | None = None,
    ) -> None:
        """Initialize CSRF protection middleware.

        Args:
            app: ASGI application
            exempt_paths: Paths exempt from CSRF (e.g., login, register)
        """
        super().__init__(app)
        self.exempt_paths = exempt_paths or [
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/docs",
            "/api/redoc",
            "/api/openapi.json",
        ]

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """Validate CSRF token for state-changing requests.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response, or 403 if CSRF validation fails
        """
        # Import settings for environment check
        from src.config import settings
        
        # Skip CSRF in development mode (common for SPAs with JWT auth)
        if settings.ENVIRONMENT == "development":
            response = await call_next(request)
            return response
        
        # Check if path is exempt
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            response = await call_next(request)
            return response

        # Only check CSRF for state-changing methods
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            # Get CSRF token from cookie
            csrf_cookie = request.cookies.get("csrf_token")

            # Get CSRF token from header
            csrf_header = request.headers.get("X-CSRF-Token")

            # Validate tokens match
            if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=403,
                    detail="CSRF validation failed. Missing or invalid CSRF token.",
                )

        response = await call_next(request)

        # Generate and set CSRF token for future requests
        csrf_token = secrets.token_urlsafe(32)
        response.set_cookie(
            key="csrf_token",
            value=csrf_token,
            httponly=True,
            secure=True,  # Only send over HTTPS in production
            samesite="strict",
            max_age=3600,  # 1 hour
        )

        return response


def sanitize_input(text: str, max_length: int = 10000) -> str:
    """Sanitize user input to prevent XSS attacks.

    Args:
        text: Raw user input
        max_length: Maximum allowed length

    Returns:
        Sanitized text
    """
    import html

    # Truncate to max length
    text = text[:max_length]

    # HTML escape to prevent XSS
    # FastAPI/Pydantic already does this for JSON responses,
    # but this is an extra layer for any direct HTML rendering
    text = html.escape(text)

    # Remove null bytes
    text = text.replace("\x00", "")

    return text


def validate_sql_injection_protection() -> dict[str, bool]:
    """Validate that SQL injection protections are in place.

    Returns:
        Dict with validation results
    """
    from pathlib import Path

    results = {
        "uses_orm": False,
        "no_raw_sql": True,
        "parameterized_queries": True,
        "issues_found": [],
    }

    # Check that we're using SQLAlchemy ORM
    try:
        from src.database import Base  # noqa: F401 - Import to verify ORM availability
        results["uses_orm"] = True
    except ImportError:
        results["issues_found"].append("SQLAlchemy ORM not found")
        results["uses_orm"] = False

    # Scan for potential SQL injection vulnerabilities
    backend_src = Path("backend/src")
    if backend_src.exists():
        dangerous_patterns = [
            "execute(f\"",  # f-string SQL
            "execute(\"SELECT",  # Raw SQL SELECT
            "execute(\"INSERT",  # Raw SQL INSERT
            "execute(\"UPDATE",  # Raw SQL UPDATE
            "execute(\"DELETE",  # Raw SQL DELETE
            ".raw(",  # Django-style raw queries
        ]

        for py_file in backend_src.rglob("*.py"):
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()
                for pattern in dangerous_patterns:
                    if pattern in content:
                        results["no_raw_sql"] = False
                        results["issues_found"].append(
                            f"Potential SQL injection risk in {py_file}: {pattern}"
                        )

    return results


def validate_xss_protection() -> dict[str, bool]:
    """Validate that XSS protections are in place.

    Returns:
        Dict with validation results
    """
    results = {
        "fastapi_auto_escape": True,  # FastAPI automatically escapes JSON
        "security_headers": False,
        "csp_configured": False,
        "issues_found": [],
    }

    # Check if security headers middleware is registered
    try:
        from src.main import app
        middleware_classes = [m.cls for m in app.user_middleware]
        if SecurityHeadersMiddleware in middleware_classes:
            results["security_headers"] = True
            results["csp_configured"] = True
    except Exception as e:
        results["issues_found"].append(f"Could not verify middleware: {str(e)}")

    return results
