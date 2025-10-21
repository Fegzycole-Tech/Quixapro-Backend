"""Centralized response utilities for consistent API responses."""

from rest_framework import status
from rest_framework.response import Response
from typing import Any, Dict, Optional


def success_response(
    data: Optional[Dict[str, Any]] = None,
    message: str = None,
    status_code: int = status.HTTP_200_OK
) -> Response:
    """
    Create a standardized success response.

    Args:
        data: Response data
        message: Success message
        status_code: HTTP status code

    Returns:
        Response object
    """
    response_data = {}
    if data:
        response_data.update(data)
    if message:
        response_data['message'] = message

    return Response(response_data, status=status_code)


def error_response(
    detail: str,
    error_code: str = None,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    errors: Optional[Dict[str, Any]] = None
) -> Response:
    """
    Create a standardized error response.

    Args:
        detail: Error message
        error_code: Machine-readable error code
        status_code: HTTP status code
        errors: Additional error details

    Returns:
        Response object
    """
    response_data = {'detail': detail}

    if error_code:
        response_data['error_code'] = error_code

    if errors:
        response_data['errors'] = errors

    return Response(response_data, status=status_code)


def service_unavailable_response(
    detail: str = "Service temporarily unavailable",
    error_code: str = "SERVICE_UNAVAILABLE"
) -> Response:
    """
    Create a 503 Service Unavailable response.

    Args:
        detail: Error message
        error_code: Error code

    Returns:
        Response object
    """
    return error_response(
        detail=detail,
        error_code=error_code,
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE
    )


def internal_server_error_response(
    detail: str = "An unexpected error occurred",
    error_code: str = "INTERNAL_SERVER_ERROR"
) -> Response:
    """
    Create a 500 Internal Server Error response.

    Args:
        detail: Error message
        error_code: Error code

    Returns:
        Response object
    """
    return error_response(
        detail=detail,
        error_code=error_code,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
