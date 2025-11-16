"""Base Pydantic schemas for API responses."""
from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Error detail schema."""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    field: str | None = Field(None, description="Field name for validation errors")


class ResponseMetadata(BaseModel):
    """Response metadata schema."""

    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    request_id: str | None = Field(None, description="Request ID for tracing")


class SuccessResponse(BaseModel, Generic[T]):
    """Generic success response schema."""

    status: str = Field("success", description="Response status")
    data: T = Field(..., description="Response data")
    metadata: ResponseMetadata = Field(
        default_factory=ResponseMetadata,
        description="Response metadata",
    )


class ErrorResponse(BaseModel):
    """Error response schema."""

    status: str = Field("error", description="Response status")
    error: ErrorDetail = Field(..., description="Error details")
    metadata: ResponseMetadata = Field(
        default_factory=ResponseMetadata,
        description="Response metadata",
    )


class PaginationMeta(BaseModel):
    """Pagination metadata schema."""

    page: int = Field(..., ge=1, description="Current page number (1-indexed)")
    page_size: int = Field(..., ge=1, le=100, description="Items per page")
    total_items: int = Field(..., ge=0, description="Total number of items")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response schema."""

    status: str = Field("success", description="Response status")
    data: list[T] = Field(..., description="List of items")
    pagination: PaginationMeta = Field(..., description="Pagination metadata")
    metadata: ResponseMetadata = Field(
        default_factory=ResponseMetadata,
        description="Response metadata",
    )


def create_success_response(data: Any, request_id: str | None = None) -> dict:
    """
    Create success response dictionary.

    Args:
        data: Response data
        request_id: Optional request ID for tracing

    Returns:
        Success response dictionary
    """
    return {
        "status": "success",
        "data": data,
        "metadata": {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
        },
    }


def create_error_response(
    code: str,
    message: str,
    field: str | None = None,
    request_id: str | None = None,
) -> dict:
    """
    Create error response dictionary.

    Args:
        code: Error code
        message: Human-readable error message
        field: Optional field name for validation errors
        request_id: Optional request ID for tracing

    Returns:
        Error response dictionary
    """
    return {
        "status": "error",
        "error": {
            "code": code,
            "message": message,
            "field": field,
        },
        "metadata": {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
        },
    }


def create_paginated_response(
    items: list[Any],
    page: int,
    page_size: int,
    total_items: int,
    request_id: str | None = None,
) -> dict:
    """
    Create paginated response dictionary.

    Args:
        items: List of items for current page
        page: Current page number (1-indexed)
        page_size: Items per page
        total_items: Total number of items
        request_id: Optional request ID for tracing

    Returns:
        Paginated response dictionary
    """
    total_pages = (total_items + page_size - 1) // page_size  # Ceiling division
    has_next = page < total_pages
    has_prev = page > 1

    return {
        "status": "success",
        "data": items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_items": total_items,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_prev": has_prev,
        },
        "metadata": {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
        },
    }
