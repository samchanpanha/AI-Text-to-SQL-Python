"""
Log retention — automated cleanup of old log entries.
Can be called manually or scheduled as a periodic APScheduler job.
"""

import logging
from datetime import datetime, timedelta

from app.database.connection import SessionLocal
from app.database.models import AuditLog, LlmCallLog, TaskExecutionLog
from config.app import Settings


settings = Settings()
logger = logging.getLogger("app.logging.cleanup")


def cleanup_logs(days: int | None = None):
    """Delete log entries older than `days`. Defaults to LOG_DB_RETENTION_DAYS."""
    retention = days or settings.LOG_DB_RETENTION_DAYS
    cutoff = datetime.utcnow() - timedelta(days=retention)
    db = SessionLocal()

    try:
        # Audit logs
        audit_deleted = (
            db.query(AuditLog)
            .filter(AuditLog.timestamp < cutoff)
            .delete(synchronize_session=False)
        )

        # LLM call logs
        llm_deleted = (
            db.query(LlmCallLog)
            .filter(LlmCallLog.timestamp < cutoff)
            .delete(synchronize_session=False)
        )

        # Task execution logs (keep these longer — always retain at least 7 days)
        task_cutoff = cutoff - timedelta(days=7)
        task_deleted = (
            db.query(TaskExecutionLog)
            .filter(TaskExecutionLog.started_at < task_cutoff)
            .delete(synchronize_session=False)
        )

        db.commit()

        logger.info(
            "Log cleanup complete: removed %d audit, %d LLM, %d task execution logs (retention: %d days)",
            audit_deleted,
            llm_deleted,
            task_deleted,
            retention,
        )

        return {
            "audit_deleted": audit_deleted,
            "llm_deleted": llm_deleted,
            "task_deleted": task_deleted,
            "retention_days": retention,
        }

    except Exception as e:
        db.rollback()
        logger.error("Log cleanup failed: %s", e)
        raise
    finally:
        db.close()
