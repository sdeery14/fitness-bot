"""Input validation helpers for common validation patterns."""
import re
from datetime import date
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status


def validate_email(email: str) -> str:
    """Validate email format.

    Args:
        email: Email address to validate

    Returns:
        Normalized email address (lowercase)

    Raises:
        HTTPException: If email format is invalid
    """
    email = email.strip().lower()

    # Basic email regex pattern
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.match(email_pattern, email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_EMAIL",
                    "message": "Invalid email format",
                }
            },
        )

    return email


def validate_password(password: str) -> None:
    """Validate password strength.

    Requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit

    Args:
        password: Password to validate

    Raises:
        HTTPException: If password doesn't meet requirements
    """
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "WEAK_PASSWORD",
                    "message": "Password must be at least 8 characters long",
                }
            },
        )

    if not re.search(r'[A-Z]', password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "WEAK_PASSWORD",
                    "message": "Password must contain at least one uppercase letter",
                }
            },
        )

    if not re.search(r'[a-z]', password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "WEAK_PASSWORD",
                    "message": "Password must contain at least one lowercase letter",
                }
            },
        )

    if not re.search(r'[0-9]', password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "WEAK_PASSWORD",
                    "message": "Password must contain at least one digit",
                }
            },
        )


def validate_uuid(uuid_string: str) -> UUID:
    """Validate UUID string format.

    Args:
        uuid_string: UUID string to validate

    Returns:
        UUID object

    Raises:
        HTTPException: If UUID format is invalid
    """
    try:
        return UUID(uuid_string)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_UUID",
                    "message": f"Invalid UUID format: {uuid_string}",
                }
            },
        ) from e


def validate_date_range(start_date: date, end_date: date) -> None:
    """Validate that end_date is after start_date.

    Args:
        start_date: Start date
        end_date: End date

    Raises:
        HTTPException: If date range is invalid
    """
    if end_date <= start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_DATE_RANGE",
                    "message": "End date must be after start date",
                }
            },
        )


def validate_positive_number(value: int | float, field_name: str = "value") -> None:
    """Validate that a number is positive.

    Args:
        value: Number to validate
        field_name: Name of the field (for error messages)

    Raises:
        HTTPException: If number is not positive
    """
    if value <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_VALUE",
                    "message": f"{field_name} must be a positive number",
                }
            },
        )


def validate_enum_value(value: str, allowed_values: list[str], field_name: str = "value") -> None:
    """Validate that a value is in the allowed set.

    Args:
        value: Value to validate
        allowed_values: List of allowed values
        field_name: Name of the field (for error messages)

    Raises:
        HTTPException: If value is not in allowed set
    """
    if value not in allowed_values:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_VALUE",
                    "message": f"{field_name} must be one of: {', '.join(allowed_values)}",
                }
            },
        )


def validate_pagination_params(page: int = 1, page_size: int = 20) -> tuple[int, int]:
    """Validate and normalize pagination parameters.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page

    Returns:
        Tuple of (skip, limit) for database queries

    Raises:
        HTTPException: If parameters are invalid
    """
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_PAGINATION",
                    "message": "Page number must be >= 1",
                }
            },
        )

    if page_size < 1 or page_size > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_PAGINATION",
                    "message": "Page size must be between 1 and 100",
                }
            },
        )

    skip = (page - 1) * page_size
    limit = page_size

    return skip, limit


def validate_json_structure(data: Any, required_fields: list[str]) -> None:
    """Validate that a JSON object contains required fields.

    Args:
        data: JSON data (dict)
        required_fields: List of required field names

    Raises:
        HTTPException: If required fields are missing
    """
    if not isinstance(data, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_JSON",
                    "message": "Expected JSON object",
                }
            },
        )

    missing_fields = [field for field in required_fields if field not in data]

    if missing_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "MISSING_FIELDS",
                    "message": f"Missing required fields: {', '.join(missing_fields)}",
                }
            },
        )


def sanitize_string(value: str, max_length: int | None = None) -> str:
    """Sanitize string input by trimming whitespace and limiting length.

    Args:
        value: String to sanitize
        max_length: Maximum allowed length (optional)

    Returns:
        Sanitized string

    Raises:
        HTTPException: If string exceeds max_length
    """
    value = value.strip()

    if max_length and len(value) > max_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "STRING_TOO_LONG",
                    "message": f"String length must not exceed {max_length} characters",
                }
            },
        )

    return value
