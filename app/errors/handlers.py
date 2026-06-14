"""
Global error handlers for structured API error responses.
"""

import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.logging.config import get_logger


logger = get_logger("errors")


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with structured response."""
    logger.warning(
        "HTTP %d: %s %s",
        exc.status_code,
        request.method,
        request.url.path,
        extra={"extra_data": {
            "status_code": exc.status_code,
            "path": str(request.url.path),
            "method": request.method,
            "detail": exc.detail,
        }},
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "type": "http_error",
            }
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with clear field-level messages."""
    errors = []
    for err in exc.errors():
        errors.append({
            "field": ".".join(str(l) for l in err.get("loc", [])),
            "message": err.get("msg", "Invalid value"),
            "type": err.get("type", "unknown"),
        })

    logger.warning(
        "Validation error: %s %s — %s",
        request.method, request.url.path, errors,
    )

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": 422,
                "message": "Request validation failed",
                "type": "validation_error",
                "details": errors,
            }
        },
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all for unhandled exceptions."""
    logger.exception(
        "Unhandled exception: %s %s — %s",
        request.method, request.url.path, str(exc),
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error",
                "type": "server_error",
            }
        },
    )
