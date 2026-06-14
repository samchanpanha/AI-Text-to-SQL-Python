from config.app.settings import Settings


class DevelopmentSettings(Settings):
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
