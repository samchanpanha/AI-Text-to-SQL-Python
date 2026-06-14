from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Text-to-SQL RAG"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "insecure-dev-key-change-in-production"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "text"
    LOG_OUTPUT: str = "console"
    LOG_FILE: str = ""
    LOG_MAX_BYTES: int = 10_485_760
    LOG_BACKUP_COUNT: int = 5
    LOG_DB_ENABLED: bool = True
    LOG_DB_RETENTION_DAYS: int = 30
    LOG_LLM_CALLS: bool = True

    # MySQL
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "app"
    DB_PASSWORD: str = "changeme"
    DB_NAME: str = "text_to_sql"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_MODEL_CHEAP: str = "gpt-4o-mini"
    OPENAI_MAX_TOKENS: int = 4096

    # Scheduler
    SCHEDULER_ENABLED: bool = True
    SCHEDULER_JOBSTORE: str = "sqlalchemy"

    # SMTP
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True
    SMTP_DEFAULT_FROM: str = "noreply@example.com"

    # Telegram
    TELEGRAM_BOT_TOKEN: str | None = None
    TELEGRAM_WEBHOOK_URL: str | None = None

    # Reports
    REPORT_TEMP_DIR: str = "/tmp/reports"
    REPORT_MAX_ROWS: int = 1_000_000
    REPORT_STREAM_CHUNK: int = 10_000
    REPORT_TIMEOUT_SECONDS: int = 600

    # Security
    ALLOWED_HOSTS: list[str] = ["*"]
    CORS_ORIGINS: list[str] = ["*"]
    RATE_LIMIT_PER_MINUTE: int = 60
    QUERY_TIMEOUT_SECONDS: int = 30
    QUERY_MAX_ROWS: int = 1000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )
