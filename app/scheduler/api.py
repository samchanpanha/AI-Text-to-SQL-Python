from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import (
    ScheduledTask, ReportDefinition, DeliveryConfig,
    EmailDelivery, TelegramDelivery, TaskExecutionLog,
)
from app.models.schemas import (
    TaskCreate, TaskUpdate, TaskResponse,
    ReportDefinitionCreate, ReportDefinitionResponse,
    DeliveryConfigCreate, EmailDeliveryCreate, TelegramDeliveryCreate,
    TaskExecuteResponse,
)
from app.scheduler.task_runner import run_task
from app.state import scheduler_manager


router = APIRouter(prefix="/tasks", tags=["scheduler"])


@router.post("", response_model=TaskResponse, status_code=201)
def create_task(body: TaskCreate, db: Session = Depends(get_db)):
    task = ScheduledTask(
        name=body.name,
        description=body.description,
        cron_expression=body.cron_expression,
        timezone=body.timezone,
        enabled=body.enabled,
        max_retries=body.max_retries,
        retry_delay_minutes=body.retry_delay_minutes,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    if task.enabled:
        scheduler_manager.add_job(
            job_id=f"task_{task.id}",
            func=run_task,
            cron_expression=task.cron_expression,
            args=[task.id],
        )

    return task


@router.get("", response_model=list[TaskResponse])
def list_tasks(db: Session = Depends(get_db)):
    return db.query(ScheduledTask).order_by(ScheduledTask.created_at.desc()).all()


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
    if not task:
        raise HTTPException(404, "Task not found")
    return task


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, body: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
    if not task:
        raise HTTPException(404, "Task not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)
    task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(task)

    # Reschedule
    scheduler_manager.remove_job(f"task_{task.id}")
    if task.enabled:
        scheduler_manager.add_job(
            job_id=f"task_{task.id}",
            func=run_task,
            cron_expression=task.cron_expression,
            args=[task.id],
        )

    return task


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
    if not task:
        raise HTTPException(404, "Task not found")
    scheduler_manager.remove_job(f"task_{task.id}")
    db.delete(task)
    db.commit()


@router.get("/{task_id}/reports", response_model=list[ReportDefinitionResponse])
def list_reports(task_id: int, db: Session = Depends(get_db)):
    return db.query(ReportDefinition).filter(ReportDefinition.task_id == task_id).order_by(ReportDefinition.sort_order).all()


@router.post("/{task_id}/reports", response_model=ReportDefinitionResponse, status_code=201)
def add_report(task_id: int, body: ReportDefinitionCreate, db: Session = Depends(get_db)):
    task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
    if not task:
        raise HTTPException(404, "Task not found")
    report = ReportDefinition(
        task_id=task_id,
        name=body.name,
        sql_query=body.sql_query,
        format=body.format,
        sheet_name=body.sheet_name,
        sort_order=body.sort_order,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.delete("/{task_id}/reports/{report_id}", status_code=204)
def delete_report(task_id: int, report_id: int, db: Session = Depends(get_db)):
    report = db.query(ReportDefinition).filter(
        ReportDefinition.id == report_id,
        ReportDefinition.task_id == task_id,
    ).first()
    if not report:
        raise HTTPException(404, "Report not found")
    db.delete(report)
    db.commit()


@router.post("/{task_id}/delivery", status_code=201)
def add_delivery(
    task_id: int,
    body: DeliveryConfigCreate,
    email_body: EmailDeliveryCreate | None = None,
    telegram_body: TelegramDeliveryCreate | None = None,
    db: Session = Depends(get_db),
):
    task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
    if not task:
        raise HTTPException(404, "Task not found")

    delivery = DeliveryConfig(
        task_id=task_id,
        type=body.type,
        name=body.name,
        enabled=body.enabled,
    )
    db.add(delivery)
    db.flush()

    if body.type == "email" and email_body:
        email = EmailDelivery(
            delivery_config_id=delivery.id,
            to_recipients=email_body.to_recipients,
            cc_recipients=email_body.cc_recipients,
            bcc_recipients=email_body.bcc_recipients,
            subject_template=email_body.subject_template,
            body_template=email_body.body_template,
            attachment_type=email_body.attachment_type,
        )
        db.add(email)

    elif body.type == "telegram" and telegram_body:
        tg = TelegramDelivery(
            delivery_config_id=delivery.id,
            chat_id=telegram_body.chat_id,
            bot_token=telegram_body.bot_token,
            message_template=telegram_body.message_template,
        )
        db.add(tg)

    db.commit()
    return {"id": delivery.id, "type": body.type}


@router.post("/{task_id}/execute", response_model=TaskExecuteResponse)
def execute_task_now(task_id: int, db: Session = Depends(get_db)):
    task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
    if not task:
        raise HTTPException(404, "Task not found")

    from threading import Thread
    thread = Thread(target=run_task, args=(task_id,), daemon=True)
    thread.start()

    return TaskExecuteResponse(
        task_id=task_id,
        status="started",
        started_at=datetime.utcnow(),
    )


@router.get("/{task_id}/logs")
def list_logs(task_id: int, db: Session = Depends(get_db)):
    return db.query(TaskExecutionLog).filter(
        TaskExecutionLog.task_id == task_id
    ).order_by(TaskExecutionLog.started_at.desc()).limit(50).all()
