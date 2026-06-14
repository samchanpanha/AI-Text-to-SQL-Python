"""
Enhanced health check endpoint.
Reports status of all system dependencies.
"""

import time
import os
import logging

from sqlalchemy import text

from app.database.connection import engine
from config.app import Settings
from app.logging.config import get_logger


settings = Settings()
logger = get_logger("monitoring")


async def health():
    """Comprehensive health check with dependency status."""
    checks = {
        "status": "healthy",
        "app": _check_app(),
        "database": _check_database(),
        "llm": _check_llm(),
        "disk": _check_disk(),
        "uptime": _get_uptime(),
    }

    overall_status = "healthy"
    for name, check in checks.items():
        if isinstance(check, dict) and check.get("status") == "unhealthy":
            overall_status = "degraded"
            checks["status"] = overall_status

    checks["status"] = overall_status
    checks["timestamp"] = time.time()

    return checks


def _check_app() -> dict:
    return {
        "status": "healthy",
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "environment": settings.APP_ENV,
        "debug": settings.DEBUG,
    }


def _check_database() -> dict:
    try:
        start = time.time()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        latency_ms = int((time.time() - start) * 1000)
        return {
            "status": "healthy",
            "host": settings.DB_HOST,
            "database": settings.DB_NAME,
            "latency_ms": latency_ms,
        }
    except Exception as e:
        logger.error("Database health check failed: %s", e)
        return {
            "status": "unhealthy",
            "host": settings.DB_HOST,
            "database": settings.DB_NAME,
            "error": str(e),
        }


def _check_llm() -> dict:
    if not settings.OPENAI_API_KEY:
        return {
            "status": "unhealthy",
            "message": "No API key configured",
        }
    return {
        "status": "healthy",
        "model": settings.OPENAI_MODEL,
        "model_cheap": settings.OPENAI_MODEL_CHEAP,
    }


def _check_disk() -> dict:
    try:
        import shutil
        usage = shutil.disk_usage(settings.REPORT_TEMP_DIR)
        free_gb = usage.free / (1024 ** 3)
        total_gb = usage.total / (1024 ** 3)
        used_pct = round((1 - usage.free / usage.total) * 100, 1)

        return {
            "status": "healthy" if free_gb > 1 else "degraded",
            "path": settings.REPORT_TEMP_DIR,
            "free_gb": round(free_gb, 2),
            "total_gb": round(total_gb, 2),
            "used_pct": used_pct,
        }
    except Exception as e:
        return {
            "status": "unknown",
            "error": str(e),
        }


_start_time = time.time()


def _get_uptime() -> float:
    return round(time.time() - _start_time, 2)
