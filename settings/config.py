from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    DEV: bool = False

    BACKEND_SERVICE_HOST: str = 'backend'
    BACKEND_SERVICE_PORT: int = 8000

    REDIS_HOST: str = 'redis'
    REDIS_PORT: int = 6379
    REDIS_USER: str = 'default'
    REDIS_PASSWORD: SecretStr = 'your_strong_password'
    REDIS_DATABASE: int = 0

    REDIS_ANSWER_QUEUE: str = 'to_answer_message'
    REDIS_SENT_QUEUE: str = 'sent_message'

    TELEGRAM_BOT_TOKEN: SecretStr = ''

    class Config:
        env_file = Path(BASE_DIR, 'settings', 'env')


settings = Settings()

