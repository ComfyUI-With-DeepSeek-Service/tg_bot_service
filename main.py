import asyncio
import logging

from aiogram.fsm.storage.base import DefaultKeyBuilder
from redis import asyncio as aioredis

from aiogram import Bot
from aiogram import Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram_dialog.setup import setup_dialogs
from loguru import logger

from settings.config import settings

logging.basicConfig(level=logging.INFO)


async def main():
    # Initialize bot and dispatcher
    redis = await aioredis.from_url(f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}')
    storage = RedisStorage(redis=redis, key_builder=DefaultKeyBuilder(with_destiny=True))
    logger.debug(f'Bot token: {settings.BOT_TOKEN.get_secret_value()}')

    bot = Bot(token=settings.BOT_TOKEN.get_secret_value())
    dp = Dispatcher(storage=storage)

    # Register all handlers
    setup_dialogs(dp)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
