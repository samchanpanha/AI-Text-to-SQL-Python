import time
import uuid
import logging

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from config.app import Settings


settings = Settings()
logger = logging.getLogger("app.access")


class RequestLogMiddleware(BaseHTTPMiddleware):
    """Log every HTTP request with timing, status, and metadata."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start = time.time()

        # Store request_id in request state for downstream use
        request.state.request_id = request_id
        request.state.start_time = start

        response: Response = await call_next(request)
        duration_ms = int((time.time() - start) * 1000)

        extra = {
            "request_id": request_id,
            "duration_ms": duration_ms,
            "status_code": response.status_code,
            "method": request.method,
            "path": request.url.path,
            "query_string": str(request.url.query),
            "client_ip": request.client.host if request.client else "unknown",
        }

        log_level = (
            logging.WARNING
            if response.status_code >= 400
            else logging.ERROR
            if response.status_code >= 500
            else logging.INFO
        )

        logger.log(
            log_level,
            "%s %s → %d (%dms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            extra={"extra_data": extra},
        )

        # Persist to DB audit log (fire-and-forget)
        if settings.LOG_DB_ENABLED:
            _write_audit_log_async(extra)

        return response


def _write_audit_log_async(data: dict):
    """Insert audit log record in background thread."""
    from threading import Thread

    thread = Thread(target=_write_audit_log_sync, args=(data,), daemon=True)
    thread.start()


def _write_audit_log_sync(data: dict):
    """Write audit log to database synchronously."""
    try:
        from app.database.connection import SessionLocal
        from app.database.models import AuditLog

        db = SessionLocal()
        try:
            entry = AuditLog(
                level=data.get("status_code", 200),
                logger_name="app.access",
                message=f"{data.get('method', '')} {data.get('path', '')} → {data.get('status_code', 0)}",
                module="middleware",
                function="dispatch",
                request_id=data.get("request_id", ""),
                user_ip=data.get("client_ip", ""),
                method=data.get("method", ""),
                path=data.get("path", ""),
                status_code=data.get("status_code", 0),
                duration_ms=data.get("duration_ms", 0),
                metadata=data,
            )
            db.add(entry)
            db.commit()
        finally:
            db.close()
    except Exception:
        pass  # fail silently — don't break request for logging
