"""
Admin dashboard endpoints — system stats, user management, configuration.
All endpoints require admin role.
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import (
    User, AuditLog, LlmCallLog, TaskExecutionLog,
    ScheduledTask, ReportDefinition,
)
from app.auth.dependencies import require_admin


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard")
def get_dashboard(
    days: int = 7,
    _=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """System dashboard with key metrics."""
    cutoff = datetime.utcnow() - timedelta(days=days)

    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    total_tasks = db.query(ScheduledTask).count()
    active_tasks = db.query(ScheduledTask).filter(ScheduledTask.enabled == True).count()
    total_reports = db.query(ReportDefinition).count()

    # API requests last N days
    api_requests = db.query(AuditLog).filter(AuditLog.timestamp >= cutoff).count()

    # Errors last N days
    errors_5xx = (
        db.query(AuditLog)
        .filter(AuditLog.timestamp >= cutoff, AuditLog.status_code >= 500)
        .count()
    )

    # LLM calls last N days
    llm_calls = (
        db.query(LlmCallLog)
        .filter(LlmCallLog.timestamp >= cutoff, LlmCallLog.success == 1)
        .count()
    )
    llm_tokens = (
        db.query(func.sum(LlmCallLog.tokens_total))
        .filter(LlmCallLog.timestamp >= cutoff, LlmCallLog.success == 1)
        .scalar() or 0
    )

    # Task executions
    task_runs = (
        db.query(TaskExecutionLog)
        .filter(TaskExecutionLog.started_at >= cutoff)
        .count()
    )
    task_failures = (
        db.query(TaskExecutionLog)
        .filter(TaskExecutionLog.started_at >= cutoff, TaskExecutionLog.status == "failed")
        .count()
    )

    # Average response time
    avg_duration = (
        db.query(func.avg(AuditLog.duration_ms))
        .filter(AuditLog.timestamp >= cutoff, AuditLog.duration_ms > 0)
        .scalar() or 0
    )

    return {
        "period_days": days,
        "users": {
            "total": total_users,
            "active": active_users,
        },
        "tasks": {
            "total": total_tasks,
            "active": active_tasks,
            "reports_defined": total_reports,
        },
        "api": {
            "requests": api_requests,
            "errors_5xx": errors_5xx,
            "avg_duration_ms": round(float(avg_duration), 2),
        },
        "llm": {
            "total_calls": llm_calls,
            "total_tokens": llm_tokens,
        },
        "scheduler": {
            "task_executions": task_runs,
            "failed_executions": task_failures,
        },
    }


@router.get("/errors/recent")
def get_recent_errors(
    limit: int = 20,
    _=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Most recent 5xx errors."""
    logs = (
        db.query(AuditLog)
        .filter(AuditLog.status_code >= 500)
        .order_by(desc(AuditLog.timestamp))
        .limit(limit)
        .all()
    )
    return [
        {
            "id": log.id,
            "timestamp": log.timestamp.isoformat() if log.timestamp else "",
            "method": log.method,
            "path": log.path,
            "status_code": log.status_code,
            "duration_ms": log.duration_ms,
            "message": log.message,
        }
        for log in logs
    ]


@router.get("/system")
def get_system_info(
    _=Depends(require_admin),
):
    """System configuration overview (no secrets)."""
    from config.app import Settings

    s = Settings()
    return {
        "app": {
            "name": s.APP_NAME,
            "environment": s.APP_ENV,
            "debug": s.DEBUG,
        },
        "database": {
            "host": s.DB_HOST,
            "name": s.DB_NAME,
            "pool_size": s.DB_POOL_SIZE,
        },
        "llm": {
            "model": s.OPENAI_MODEL,
            "cheap_model": s.OPENAI_MODEL_CHEAP,
            "max_tokens": s.OPENAI_MAX_TOKENS,
        },
        "scheduler": {
            "enabled": s.SCHEDULER_ENABLED,
        },
        "security": {
            "rate_limit_per_minute": s.RATE_LIMIT_PER_MINUTE,
            "query_max_rows": s.QUERY_MAX_ROWS,
            "query_timeout_seconds": s.QUERY_TIMEOUT_SECONDS,
        },
        "logging": {
            "level": s.LOG_LEVEL,
            "format": s.LOG_FORMAT,
            "db_enabled": s.LOG_DB_ENABLED,
            "retention_days": s.LOG_DB_RETENTION_DAYS,
            "llm_call_logging": s.LOG_LLM_CALLS,
        },
    }
