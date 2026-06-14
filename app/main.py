import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError

from config.app import Settings
from app.database.connection import engine
from app.router.query import router as query_router
from app.router.n8n import router as n8n_router
from app.router.admin import router as admin_router
from app.scheduler.api import router as scheduler_router
from app.logging.api import router as log_router
from app.auth.api import router as auth_router
from app.auth.jwt import create_admin_user
from app.webchat.ws_handler import router as ws_router
from app.logging.middleware import RequestLogMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.logging.config import setup_logging
from app.errors.handlers import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler,
)
from app.state import scheduler_manager, telegram_bot


settings = Settings()

# Initialize logging
setup_logging()

# Ensure required directories exist
for dir_path in [
    os.path.dirname(settings.LOG_FILE) if settings.LOG_FILE else None,
    settings.REPORT_TEMP_DIR,
]:
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Bootstrap default admin on first run
    create_admin_user()

    if settings.SCHEDULER_ENABLED:
        scheduler_manager.start()
        _schedule_log_cleanup()

    if settings.TELEGRAM_BOT_TOKEN:
        await telegram_bot.set_webhook()

    yield

    if settings.SCHEDULER_ENABLED:
        scheduler_manager.shutdown()
    await engine.dispose()


def _schedule_log_cleanup():
    """Schedule daily log cleanup at 3:00 AM."""
    from app.logging.cleanup import cleanup_logs

    scheduler_manager.add_job(
        job_id="log_cleanup",
        func=cleanup_logs,
        cron_expression="0 3 * * *",
    )


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

# ── Middleware (order matters: rate limit → request log → cors) ──
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestLogMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Error handlers ──
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# ── Routes ──
app.include_router(auth_router, prefix="/api")
app.include_router(query_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(n8n_router, prefix="/api")
app.include_router(scheduler_router, prefix="/api")
app.include_router(log_router, prefix="/api")
app.include_router(ws_router)

app.mount("/chat", StaticFiles(directory="app/webchat/static", html=True), name="chat")


# Built-in health check (registered directly so it always works)
@app.get("/health")
async def health():
    from app.monitoring.health import health as health_check
    return await health_check()


@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    update = await request.json()
    await telegram_bot.handle_update(update)
    return {"ok": True}
