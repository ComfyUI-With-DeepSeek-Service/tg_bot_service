import asyncio
import logging

from aiogram import Dispatcher
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisStorage
# from aiogram_dialog.setup import setup_dialogs
from loguru import logger

from receiver.app import setup_handlers
from responser.app import MessageQueueWorker
from services.redis import redis_client
from services.tg_bot import tg_bot

logging.basicConfig(level=logging.INFO)


async def main():
    # Initialize bot and dispatcher

    storage = RedisStorage(redis=redis_client, key_builder=DefaultKeyBuilder(with_destiny=True))
    dp = Dispatcher(storage=storage)

    # Register all handlers
    # setup_dialogs(dp)
    setup_handlers(dp=dp)

    logger.info('starting bot pooling')
    tg_pooling = dp.start_polling(tg_bot)

    logger.info('starting licening')
    worker = MessageQueueWorker(redis=redis_client, tg_bot=tg_bot)
    tg_responser = worker.process_queue()

    await asyncio.gather(
        tg_pooling,
        tg_responser
    )


if __name__ == "__main__":
    asyncio.run(main())
