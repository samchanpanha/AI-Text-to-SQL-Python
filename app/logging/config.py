import logging
import sys
from logging.handlers import RotatingFileHandler

from app.logging.formatter import JsonFormatter
from config.app import Settings


settings = Settings()


def setup_logging() -> None:
    """Configure root logger with appropriate handlers and formatters."""
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL.upper())

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Determine format
    if settings.LOG_FORMAT == "json":
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
        )

    # Console handler
    if settings.LOG_OUTPUT in ("console", "both"):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(settings.LOG_LEVEL.upper())
        root_logger.addHandler(console_handler)

    # File handler with rotation
    if settings.LOG_OUTPUT in ("file", "both") and settings.LOG_FILE:
        file_handler = RotatingFileHandler(
            filename=settings.LOG_FILE,
            maxBytes=settings.LOG_MAX_BYTES,
            backupCount=settings.LOG_BACKUP_COUNT,
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(settings.LOG_LEVEL.upper())
        root_logger.addHandler(file_handler)

    # Set levels for noisy third-party loggers
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    root_logger.info(
        "Logging configured",
        extra={
            "extra_data": {
                "level": settings.LOG_LEVEL,
                "format": settings.LOG_FORMAT,
                "output": settings.LOG_OUTPUT,
                "file": settings.LOG_FILE,
            }
        },
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the application namespace."""
    return logging.getLogger(f"app.{name}")
