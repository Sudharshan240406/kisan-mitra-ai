import logging
import traceback
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.exceptions import KisanMitraException

logger = logging.getLogger("kisan_mitra_ai")

async def kisan_mitra_exception_handler(request: Request, exc: KisanMitraException) -> JSONResponse:
    """
    Handle application-specific KisanMitra exceptions.
    """
    logger.error(
        f"[Exception Handled] {exc.__class__.__name__}: {exc.message}",
        extra={"extra_fields": {"details": exc.details, "path": request.url.path}}
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details
        }
    )

async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handle standard HTTP exceptions. Preserves dictionary/object detail payloads.
    """
    logger.warning(
        f"[HTTP Exception Handled] {exc.status_code}: {exc.detail}",
        extra={"extra_fields": {"path": request.url.path}}
    )
    
    if isinstance(exc.detail, dict):
        content = {
            "error_code": "HTTPException",
            "message": exc.detail.get("message") or exc.detail.get("status") or "HTTP exception occurred.",
            "details": exc.detail,
            "detail": exc.detail  # Backward compatibility
        }
    else:
        content = {
            "error_code": "HTTPException",
            "message": str(exc.detail),
            "details": {}
        }
        
    return JSONResponse(
        status_code=exc.status_code,
        content=content
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle request schema validation exceptions.
    """
    errors = exc.errors()
    logger.warning(
        f"[Validation Exception Handled] 400 Bad Request: {errors}",
        extra={"extra_fields": {"path": request.url.path}}
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error_code": "RequestValidationError",
            "message": "Schema validation failed for request payload.",
            "details": {"validation_errors": errors}
        }
    )

async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected/unhandled exceptions.
    """
    tb = traceback.format_exc()
    logger.critical(
        f"[Unhandled Exception] 500 Internal Server Error: {exc}\n{tb}",
        extra={"extra_fields": {"path": request.url.path}}
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "InternalServerError",
            "message": "An unexpected error occurred on the server.",
            "details": {"error_type": exc.__class__.__name__}
        }
    )
