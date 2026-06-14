import time
import os
import json
import tempfile
from datetime import datetime
from zipfile import ZipFile

from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.database.models import ScheduledTask, ReportDefinition, DeliveryConfig, TaskExecutionLog
from app.reports.generator import generate_excel
from app.delivery.email import send_email_report
from app.delivery.telegram import send_telegram_report
from config.app import Settings


settings = Settings()


def run_task(task_id: int):
    """Execute a scheduled task: generate all reports → zip if needed → deliver."""
    db = SessionLocal()
    start_time = time.time()
    log = TaskExecutionLog(
        task_id=task_id,
        status="running",
        started_at=datetime.utcnow(),
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    try:
        task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
        if not task:
            log.status = "failed"
            log.error_message = "Task not found"
            db.commit()
            return

        reports = db.query(ReportDefinition).filter(
            ReportDefinition.task_id == task_id
        ).order_by(ReportDefinition.sort_order).all()

        deliveries = db.query(DeliveryConfig).filter(
            DeliveryConfig.task_id == task_id,
            DeliveryConfig.enabled == True,
        ).all()

        generated_files = []
        total_rows = 0

        for report in reports:
            try:
                file_path = generate_excel(
                    sql_query=report.sql_query,
                    sheet_name=report.sheet_name,
                    output_dir=settings.REPORT_TEMP_DIR,
                    filename_prefix=f"task_{task_id}_{report.id}",
                )
                generated_files.append({
                    "report_id": report.id,
                    "name": report.name,
                    "path": file_path,
                    "format": report.format,
                })
            except Exception as e:
                log.error_message = f"Report '{report.name}' failed: {str(e)}"

        # Wait for all files generated — then zip if multiple files
        final_files = []
        if len(generated_files) > 1:
            zip_path = _create_zip(task_id, generated_files)
            final_files.append({
                "type": "zip",
                "path": zip_path,
                "name": f"report_{task_id}.zip",
            })
        else:
            for f in generated_files:
                final_files.append({
                    "type": f["format"],
                    "path": f["path"],
                    "name": f"{f['name']}.{f['format']}",
                })

        log.files_generated = json.dumps(final_files)
        delivery_results = []

        for delivery in deliveries:
            try:
                if delivery.type == "email":
                    email_cfg = delivery.email_config
                    if email_cfg:
                        send_email_report(
                            to=email_cfg.to_recipients.split(","),
                            cc=email_cfg.cc_recipients.split(",") if email_cfg.cc_recipients else [],
                            bcc=email_cfg.bcc_recipients.split(",") if email_cfg.bcc_recipients else [],
                            subject_template=email_cfg.subject_template,
                            body_template=email_cfg.body_template,
                            files=final_files,
                            task=task,
                        )
                        delivery_results.append({"type": "email", "status": "sent"})
                elif delivery.type == "telegram":
                    tg_cfg = delivery.telegram_config
                    if tg_cfg:
                        send_telegram_report(
                            chat_id=tg_cfg.chat_id,
                            bot_token=tg_cfg.bot_token,
                            message_template=tg_cfg.message_template,
                            files=final_files,
                            task=task,
                        )
                        delivery_results.append({"type": "telegram", "status": "sent"})
            except Exception as e:
                delivery_results.append({"type": delivery.type, "status": "failed", "error": str(e)})

        log.delivery_results = json.dumps(delivery_results)
        log.status = "success" if not log.error_message else "partial"
        log.completed_at = datetime.utcnow()
        log.duration_ms = int((time.time() - start_time) * 1000)
        log.rows_processed = total_rows
        db.commit()

    except Exception as e:
        log.status = "failed"
        log.error_message = str(e)
        log.completed_at = datetime.utcnow()
        log.duration_ms = int((time.time() - start_time) * 1000)
        db.commit()
    finally:
        db.close()
        _cleanup_temp_files(generated_files, final_files)


def _create_zip(task_id: int, files: list[dict]) -> str:
    """Zip all generated files after they're all complete."""
    os.makedirs(settings.REPORT_TEMP_DIR, exist_ok=True)
    zip_name = f"report_{task_id}_{int(time.time())}.zip"
    zip_path = os.path.join(settings.REPORT_TEMP_DIR, zip_name)

    with ZipFile(zip_path, "w") as zf:
        for f in files:
            file_path = f.get("path")
            if file_path and os.path.exists(file_path):
                zf.write(file_path, arcname=os.path.basename(file_path))

    return zip_path


def _cleanup_temp_files(generated: list[dict], final: list[dict]):
    """Remove temporary files after delivery."""
    for f in generated:
        p = f.get("path")
        if p and os.path.exists(p) and "tmp" in p:
            try:
                os.remove(p)
            except Exception:
                pass
    for f in final:
        p = f.get("path")
        if p and os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass
