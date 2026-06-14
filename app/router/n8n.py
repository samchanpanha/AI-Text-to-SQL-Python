"""
n8n-compatible webhook endpoints.
Returns data in flat, easy-to-parse formats that n8n HTTP Request nodes consume cleanly.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.dependencies import require_auth

from app.models.schemas import QueryRequest
from app.router.query import query as query_endpoint
from app.database.schema import get_table_schemas, format_schema_for_prompt
from app.scheduler.task_runner import run_task
from app.database.connection import SessionLocal
from app.database.models import ScheduledTask


router = APIRouter(prefix="/n8n", tags=["n8n"])


# ── Request Models ──

class N8nQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)

class N8nQueryAndSendRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    send_to: str = Field(..., pattern="^(email|telegram)$")
    email_to: str | None = None
    email_subject: str | None = "Query Results"
    telegram_chat_id: str | None = None

class N8nExecuteTaskRequest(BaseModel):
    task_id: int


# ── Endpoints ──

@router.post("/webhook/query")
async def n8n_query(body: N8nQueryRequest, _=Depends(require_auth)):
    """Webhook: question in → answer + metadata out. Main n8n entry point."""
    try:
        result = await query_endpoint(QueryRequest(question=body.question))
        return {
            "output": result.answer,
            "sql_query": result.sql_query or "",
            "row_count": result.row_count or 0,
            "execution_time_ms": result.execution_time_ms or 0,
        }
    except HTTPException as e:
        return {
            "output": f"Error: {e.detail}",
            "sql_query": "",
            "row_count": 0,
            "execution_time_ms": 0,
        }


@router.post("/webhook/query-simple")
async def n8n_query_simple(body: N8nQueryRequest, _=Depends(require_auth)):
    """Webhook: question in → plain answer out (no metadata)."""
    try:
        result = await query_endpoint(QueryRequest(question=body.question))
        return {"output": result.answer}
    except HTTPException as e:
        return {"output": f"Error: {e.detail}"}


@router.post("/webhook/execute-task")
async def n8n_execute_task(body: N8nExecuteTaskRequest, _=Depends(require_auth)):
    """Webhook: trigger a scheduled task immediately. Returns once files are ready."""
    db = SessionLocal()
    try:
        task = db.query(ScheduledTask).filter(ScheduledTask.id == body.task_id).first()
        if not task:
            return {"status": "error", "message": "Task not found"}

        # Run synchronously so n8n waits for completion
        run_task(body.task_id)

        # Get the latest log
        log = (
            db.query(ScheduledTask)
            .filter(ScheduledTask.id == body.task_id)
            .first()
        )
        return {
            "status": "completed",
            "task_id": body.task_id,
            "task_name": task.name,
        }
    finally:
        db.close()


@router.post("/webhook/query-and-send")
async def n8n_query_and_send(body: N8nQueryAndSendRequest, _=Depends(require_auth)):
    """Webhook: question → query → auto-deliver results via email or Telegram."""
    try:
        query_result = await query_endpoint(QueryRequest(question=body.question))
    except HTTPException as e:
        return {"status": "error", "message": e.detail}

    if body.send_to == "email" and body.email_to:
        from app.delivery.email import send_email_report

        class MockTask:
            name = "n8n Query Result"
            description = ""

        send_email_report(
            to=[body.email_to],
            subject_template=body.email_subject or "Query Results",
            body_template="{{ task_name }}\n\n{{ answer }}",
            files=[],
            task=MockTask(),
        )
        return {
            "status": "sent",
            "channel": "email",
            "to": body.email_to,
            "output": query_result.answer,
        }

    elif body.send_to == "telegram" and body.telegram_chat_id:
        from app.delivery.telegram import send_telegram_report

        class MockTask:
            name = "n8n Query Result"
            description = ""

        send_telegram_report(
            chat_id=body.telegram_chat_id,
            bot_token="",  # uses default from settings
            files=[],
            task=MockTask(),
            message_template=query_result.answer,
        )
        return {
            "status": "sent",
            "channel": "telegram",
            "to": body.telegram_chat_id,
            "output": query_result.answer,
        }

    return {"status": "error", "message": "Invalid delivery configuration"}


@router.get("/tasks")
async def n8n_list_tasks(_=Depends(require_auth)):
    """List available tasks — n8n can use this for dynamic options."""
    db = SessionLocal()
    try:
        tasks = db.query(ScheduledTask).order_by(ScheduledTask.name).all()
        return [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description or "",
                "cron_expression": t.cron_expression,
                "enabled": t.enabled,
                "report_count": len(t.reports),
            }
            for t in tasks
        ]
    finally:
        db.close()


@router.get("/schema")
async def n8n_schema(_=Depends(require_auth)):
    """Return database schema as structured JSON for n8n processing."""
    schemas = get_table_schemas()
    return schemas


@router.get("/schema/text")
async def n8n_schema_text(_=Depends(require_auth)):
    """Return database schema as plain text for LLM prompts."""
    schemas = get_table_schemas()
    return {"schema": format_schema_for_prompt(schemas)}
