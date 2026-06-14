"""Shared application state to avoid circular imports."""

from app.scheduler.manager import SchedulerManager
from app.delivery.telegram import TelegramBot


scheduler_manager = SchedulerManager()
telegram_bot = TelegramBot()
