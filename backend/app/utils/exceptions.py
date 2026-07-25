from fastapi import HTTPException, status
from typing import Optional, Any, Dict
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class APIException(HTTPException):
    """Custom API exception."""
    
    def __init__(
        self,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detail: str = "Bad Request",
        error_code: Optional[str] = None,
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code


class ValidationException(APIException):
    """Validation error exception."""
    
    def __init__(self, detail: str, error_code: str = "VALIDATION_ERROR"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code=error_code,
        )


class NotAuthorizedException(APIException):
    """Authorization exception."""
    
    def __init__(self, detail: str = "Not authorized"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="UNAUTHORIZED",
        )


class ForbiddenException(APIException):
    """Forbidden exception."""
    
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="FORBIDDEN",
        )


class NotFoundException(APIException):
    """Not found exception."""
    
    def __init__(self, detail: str = "Not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="NOT_FOUND",
        )


class ConflictException(APIException):
    """Conflict exception."""
    
    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code="CONFLICT",
        )


class RateLimitException(APIException):
    """Rate limit exception."""
    
    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            error_code="RATE_LIMITED",
        )


class ExternalServiceException(APIException):
    """External service error exception."""
    
    def __init__(self, service: str, detail: str):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{service}: {detail}",
            error_code="EXTERNAL_SERVICE_ERROR",
        )


def create_response(
    success: bool,
    status_code: int,
    message: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    error: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create standardized API response."""
    return {
        "success": success,
        "statusCode": status_code,
        "message": message,
        "data": data,
        "error": error,
        "timestamp": datetime.utcnow().isoformat(),
    }


def create_paginated_response(
    items: list,
    total: int,
    page: int,
    limit: int,
) -> Dict[str, Any]:
    """Create paginated response."""
    total_pages = (total + limit - 1) // limit
    return {
        "items": items,
        "pagination": {
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        },
    }
