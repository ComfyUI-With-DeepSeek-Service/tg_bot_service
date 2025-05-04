from loguru import logger
from redis.asyncio import Redis

from settings.config import settings

REDIS_URL = (
    f'redis://{settings.REDIS_USER}:{settings.REDIS_PASSWORD.get_secret_value()}@'
    f'{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DATABASE}'
)

logger.debug(f'Init redis client')

redis_client = Redis.from_url(REDIS_URL)
