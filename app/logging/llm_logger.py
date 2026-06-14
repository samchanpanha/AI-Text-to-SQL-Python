import time
import logging

from config.app import Settings


settings = Settings()
logger = logging.getLogger("app.llm")


def log_llm_call(
    model: str,
    system_prompt: str,
    user_prompt: str,
    response: str,
    duration_ms: int,
    success: bool = True,
    error_message: str | None = None,
    tokens_prompt: int = 0,
    tokens_completion: int = 0,
    request_id: str = "",
):
    """Log an LLM API call to database and structured log."""
    tokens_total = tokens_prompt + tokens_completion

    extra = {
        "model": model,
        "tokens_prompt": tokens_prompt,
        "tokens_completion": tokens_completion,
        "tokens_total": tokens_total,
        "duration_ms": duration_ms,
        "success": success,
        "request_id": request_id,
    }

    if success:
        logger.info(
            "LLM call: %s | %d tokens | %dms",
            model,
            tokens_total,
            duration_ms,
            extra={"extra_data": extra},
        )
    else:
        logger.error(
            "LLM call FAILED: %s | %s | %dms",
            model,
            error_message,
            duration_ms,
            extra={"extra_data": extra},
        )

    # Persist to DB
    if settings.LOG_LLM_CALLS and settings.LOG_DB_ENABLED:
        _persist_llm_call(
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response=response,
            duration_ms=duration_ms,
            success=success,
            error_message=error_message,
            tokens_prompt=tokens_prompt,
            tokens_completion=tokens_completion,
            request_id=request_id,
        )


def _persist_llm_call(
    model: str,
    system_prompt: str,
    user_prompt: str,
    response: str,
    duration_ms: int,
    success: bool,
    error_message: str | None,
    tokens_prompt: int,
    tokens_completion: int,
    request_id: str,
):
    """Write LLM call record to database."""
    try:
        from app.database.connection import SessionLocal
        from app.database.models import LlmCallLog

        db = SessionLocal()
        try:
            entry = LlmCallLog(
                model=model,
                system_prompt=system_prompt[:5000],
                user_prompt=user_prompt[:10000],
                response=response[:10000],
                tokens_prompt=tokens_prompt,
                tokens_completion=tokens_completion,
                tokens_total=tokens_prompt + tokens_completion,
                duration_ms=duration_ms,
                success=success,
                error_message=error_message[:500] if error_message else None,
                request_id=request_id,
            )
            db.add(entry)
            db.commit()
        finally:
            db.close()
    except Exception as e:
        logger.warning("Failed to persist LLM call log: %s", e)
