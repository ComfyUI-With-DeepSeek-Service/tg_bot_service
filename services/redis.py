from loguru import logger
from redis.asyncio import Redis


REDIS_URL = "redis://default:your_strong_password@localhost:6379/0"


logger.debug(f'Redis created: {REDIS_URL}')

redis_client = Redis.from_url(REDIS_URL)
