from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import desc

from app.auth.dependencies import require_admin

from app.database.connection import SessionLocal
from app.database.models import AuditLog, LlmCallLog, TaskExecutionLog


router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("/audit")
async def get_audit_logs(_=Depends(require_admin),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=500),
    level: int | None = Query(None, ge=0),
    status_code: int | None = Query(None, ge=100, le=599),
    method: str | None = None,
    path: str | None = None,
    request_id: str | None = None,
    days: int | None = Query(None, ge=1, le=365),
    from_date: str | None = None,
    to_date: str | None = None,
):
    """Query audit logs with filters and pagination."""
    db = SessionLocal()
    try:
        query = db.query(AuditLog)

        if level is not None:
            query = query.filter(AuditLog.level >= level)
        if status_code is not None:
            query = query.filter(AuditLog.status_code == status_code)
        if method:
            query = query.filter(AuditLog.method == method.upper())
        if path:
            query = query.filter(AuditLog.path.like(f"%{path}%"))
        if request_id:
            query = query.filter(AuditLog.request_id == request_id)
        if days:
            cutoff = datetime.utcnow() - timedelta(days=days)
            query = query.filter(AuditLog.timestamp >= cutoff)
        if from_date:
            query = query.filter(AuditLog.timestamp >= datetime.fromisoformat(from_date))
        if to_date:
            query = query.filter(AuditLog.timestamp <= datetime.fromisoformat(to_date))

        total = query.count()
        logs = (
            query.order_by(desc(AuditLog.timestamp))
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page,
            "logs": [
                {
                    "id": log.id,
                    "timestamp": log.timestamp.isoformat() if log.timestamp else "",
                    "level": log.level,
                    "message": log.message,
                    "module": log.module,
                    "request_id": log.request_id,
                    "method": log.method,
                    "path": log.path,
                    "status_code": log.status_code,
                    "duration_ms": log.duration_ms,
                    "user_ip": log.user_ip,
                }
                for log in logs
            ],
        }
    finally:
        db.close()


@router.get("/audit/stats")
async def get_audit_stats(_=Depends(require_admin), days: int = Query(7, ge=1, le=365)):
    """Aggregated statistics on audit logs."""
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)

        total = db.query(AuditLog).filter(AuditLog.timestamp >= cutoff).count()
        errors = (
            db.query(AuditLog)
            .filter(AuditLog.timestamp >= cutoff, AuditLog.status_code >= 500)
            .count()
        )
        warnings = (
            db.query(AuditLog)
            .filter(AuditLog.timestamp >= cutoff, AuditLog.status_code >= 400, AuditLog.status_code < 500)
            .count()
        )

        # Top paths
        from sqlalchemy import func

        top_paths = (
            db.query(AuditLog.path, func.count(AuditLog.id).label("count"))
            .filter(AuditLog.timestamp >= cutoff)
            .group_by(AuditLog.path)
            .order_by(desc("count"))
            .limit(10)
            .all()
        )

        avg_duration = (
            db.query(func.avg(AuditLog.duration_ms))
            .filter(AuditLog.timestamp >= cutoff, AuditLog.duration_ms > 0)
            .scalar()
        )

        return {
            "period_days": days,
            "total_requests": total,
            "errors_5xx": errors,
            "warnings_4xx": warnings,
            "avg_duration_ms": round(avg_duration or 0, 2),
            "top_paths": [
                {"path": path, "count": count} for path, count in top_paths
            ],
        }
    finally:
        db.close()


@router.get("/llm")
async def get_llm_logs(_=Depends(require_admin),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    model: str | None = None,
    success: bool | None = None,
    request_id: str | None = None,
    days: int | None = Query(None, ge=1, le=365),
    min_tokens: int | None = Query(None, ge=0),
    max_tokens: int | None = Query(None, ge=0),
):
    """Query LLM call logs."""
    db = SessionLocal()
    try:
        query = db.query(LlmCallLog)

        if model:
            query = query.filter(LlmCallLog.model == model)
        if success is not None:
            query = query.filter(LlmCallLog.success == (1 if success else 0))
        if request_id:
            query = query.filter(LlmCallLog.request_id == request_id)
        if days:
            cutoff = datetime.utcnow() - timedelta(days=days)
            query = query.filter(LlmCallLog.timestamp >= cutoff)
        if min_tokens is not None:
            query = query.filter(LlmCallLog.tokens_total >= min_tokens)
        if max_tokens is not None:
            query = query.filter(LlmCallLog.tokens_total <= max_tokens)

        total = query.count()
        logs = (
            query.order_by(desc(LlmCallLog.timestamp))
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return {
            "total": total,
            "page": page,
            "per_page": per_page,
            "logs": [
                {
                    "id": log.id,
                    "timestamp": log.timestamp.isoformat() if log.timestamp else "",
                    "model": log.model,
                    "tokens_prompt": log.tokens_prompt,
                    "tokens_completion": log.tokens_completion,
                    "tokens_total": log.tokens_total,
                    "duration_ms": log.duration_ms,
                    "success": bool(log.success),
                    "error_message": log.error_message,
                    "request_id": log.request_id,
                }
                for log in logs
            ],
        }
    finally:
        db.close()


@router.get("/llm/{log_id}")
async def get_llm_log_detail(log_id: int, _=Depends(require_admin)):
    """Get full detail of a specific LLM call (prompts + response)."""
    db = SessionLocal()
    try:
        log = db.query(LlmCallLog).filter(LlmCallLog.id == log_id).first()
        if not log:
            raise HTTPException(404, "LLM log not found")
        return {
            "id": log.id,
            "timestamp": log.timestamp.isoformat() if log.timestamp else "",
            "model": log.model,
            "system_prompt": log.system_prompt,
            "user_prompt": log.user_prompt,
            "response": log.response,
            "tokens_prompt": log.tokens_prompt,
            "tokens_completion": log.tokens_completion,
            "tokens_total": log.tokens_total,
            "duration_ms": log.duration_ms,
            "success": bool(log.success),
            "error_message": log.error_message,
            "request_id": log.request_id,
        }
    finally:
        db.close()


@router.get("/llm/stats")
async def get_llm_stats(_=Depends(require_admin), days: int = Query(7, ge=1, le=365)):
    """LLM usage and cost statistics."""
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        from sqlalchemy import func

        stats = (
            db.query(
                LlmCallLog.model,
                func.count(LlmCallLog.id).label("calls"),
                func.sum(LlmCallLog.tokens_prompt).label("total_prompt_tokens"),
                func.sum(LlmCallLog.tokens_completion).label("total_completion_tokens"),
                func.sum(LlmCallLog.tokens_total).label("total_tokens"),
                func.avg(LlmCallLog.duration_ms).label("avg_duration_ms"),
                func.sum(LlmCallLog.duration_ms).label("total_duration_ms"),
            )
            .filter(LlmCallLog.timestamp >= cutoff, LlmCallLog.success == 1)
            .group_by(LlmCallLog.model)
            .all()
        )

        # Approximate cost (GPT-4o: $2.50/M input, $10/M output; GPT-4o-mini: $0.15/M input, $0.60/M output)
        pricing = {
            "gpt-4o": {"input": 2.50, "output": 10.00},
            "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        }

        models = []
        total_cost = 0.0
        for row in stats:
            model = row.model or "unknown"
            p = pricing.get(model, {"input": 1.0, "output": 2.0})
            cost = (
                (row.total_prompt_tokens or 0) / 1_000_000 * p["input"]
                + (row.total_completion_tokens or 0) / 1_000_000 * p["output"]
            )
            total_cost += cost
            models.append(
                {
                    "model": model,
                    "calls": row.calls,
                    "total_prompt_tokens": row.total_prompt_tokens or 0,
                    "total_completion_tokens": row.total_completion_tokens or 0,
                    "total_tokens": row.total_tokens or 0,
                    "avg_duration_ms": round(row.avg_duration_ms or 0, 2),
                    "total_duration_ms": row.total_duration_ms or 0,
                    "estimated_cost_usd": round(cost, 4),
                }
            )

        total_calls = db.query(LlmCallLog).filter(
            LlmCallLog.timestamp >= cutoff, LlmCallLog.success == 1
        ).count()

        failed_calls = db.query(LlmCallLog).filter(
            LlmCallLog.timestamp >= cutoff, LlmCallLog.success == 0
        ).count()

        return {
            "period_days": days,
            "total_calls": total_calls,
            "failed_calls": failed_calls,
            "total_estimated_cost_usd": round(total_cost, 4),
            "models": models,
        }
    finally:
        db.close()


@router.get("/task-executions")
async def get_task_execution_logs(_=Depends(require_admin),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    task_id: int | None = None,
    status: str | None = None,
    days: int | None = Query(None, ge=1, le=365),
):
    """Query task execution logs (reports + deliveries)."""
    db = SessionLocal()
    try:
        query = db.query(TaskExecutionLog)

        if task_id:
            query = query.filter(TaskExecutionLog.task_id == task_id)
        if status:
            query = query.filter(TaskExecutionLog.status == status)
        if days:
            cutoff = datetime.utcnow() - timedelta(days=days)
            query = query.filter(TaskExecutionLog.started_at >= cutoff)

        total = query.count()
        logs = (
            query.order_by(desc(TaskExecutionLog.started_at))
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return {
            "total": total,
            "page": page,
            "per_page": per_page,
            "logs": [
                {
                    "id": log.id,
                    "task_id": log.task_id,
                    "status": log.status,
                    "started_at": log.started_at.isoformat() if log.started_at else "",
                    "completed_at": log.completed_at.isoformat() if log.completed_at else "",
                    "duration_ms": log.duration_ms,
                    "error_message": log.error_message,
                    "rows_processed": log.rows_processed,
                }
                for log in logs
            ],
        }
    finally:
        db.close()


@router.post("/cleanup")
async def trigger_log_cleanup(_=Depends(require_admin), days: int = Query(30, ge=1, le=365)):
    """Manually trigger log cleanup. Deletes logs older than `days`."""
    from app.logging.cleanup import cleanup_logs

    result = cleanup_logs(days=days)
    return {
        "status": "ok",
        "message": f"Cleaned up logs older than {days} days",
        "deleted": result,
    }
