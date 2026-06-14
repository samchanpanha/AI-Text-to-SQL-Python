from config.app.settings import Settings


class ProductionSettings(Settings):
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40
    ALLOWED_HOSTS: list[str] = []
    CORS_ORIGINS: list[str] = []
