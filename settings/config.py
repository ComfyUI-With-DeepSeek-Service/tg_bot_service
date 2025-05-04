from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    DEV: bool = False

    REDIS_HOST: str = 'redis'
    REDIS_PORT: int = 6379
    REDIS_USER: str = 'default'
    REDIS_PASSWORD: SecretStr = 'your_strong_password'
    REDIS_DATABASE: int = 0

    TELEGRAM_BOT_TOKEN: SecretStr = ''

    class Config:
        env_file = Path(BASE_DIR, 'settings', 'env')


settings = Settings()

