from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    DEV: bool = False

    REDIS_HOST: str = ''
    REDIS_PORT: int = 6379

    BOT_TOKEN: SecretStr = ''

    class Config:
        env_file = Path(BASE_DIR, 'settings', 'env')


settings = Settings()


def get_db_url(db_name: str = settings.POSTGRES_DATABASE) -> str:
    return (
        f'postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD.get_secret_value()}@'
        f'{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{db_name}'
    )

