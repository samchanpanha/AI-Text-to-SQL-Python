from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor

from app.database.connection import engine
from config.app import Settings


settings = Settings()


class SchedulerManager:
    def __init__(self):
        self.scheduler = BackgroundScheduler(
            jobstores={
                "default": SQLAlchemyJobStore(engine=engine),
            },
            executors={
                "default": ThreadPoolExecutor(20),
            },
            job_defaults={
                "coalesce": False,
                "max_instances": 1,
                "misfire_grace_time": 300,
            },
            timezone="UTC",
        )

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()

    def shutdown(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    def add_job(self, job_id: str, func, cron_expression: str, args: list = None):
        self.scheduler.add_job(
            func,
            trigger="cron",
            id=job_id,
            replace_existing=True,
            cron_expression=cron_expression,
            args=args or [],
        )

    def remove_job(self, job_id: str):
        try:
            self.scheduler.remove_job(job_id)
        except Exception:
            pass

    def pause_job(self, job_id: str):
        try:
            self.scheduler.pause_job(job_id)
        except Exception:
            pass

    def resume_job(self, job_id: str):
        try:
            self.scheduler.resume_job(job_id)
        except Exception:
            pass
