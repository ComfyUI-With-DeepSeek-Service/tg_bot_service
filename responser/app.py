# check for redis updates, send to sender msg
import asyncio
import json
import logging

from aiogram import Bot
from loguru import logger

from services.redis import redis_client
from services.tg_bot import tg_bot


class MessageQueueWorker:
    def __init__(
        self,
        to_send_queue: str = "to_send_message",
        sent_queue: str = "sent_message",
    ) -> None:
        self.redis = redis_client
        self.bot = tg_bot
        self.to_send_queue = to_send_queue
        self.sent_queue = sent_queue

    async def process_message(self, message_key: str, message_value: str) -> bool:
        """
        Process single message from queue:
        1. Parse message data
        2. Send message via aiogram
        3. Move to sent queue if successful
        """
        logger.info(f'msg: {message_key}, val: {message_value}')
        try:
            # Parse message data
            message_data = json.loads(message_key)
            chat_id = message_data["chat_id"]
            message_id = message_data["message_id"]
            text = message_value

            # Send message
            # await self.bot.send_message(
            #     chat_id=chat_id,
            #     text=text,
            #     reply_to_message_id=message_id,
            # )

            # Move to sent queue
            await self.redis.hset(self.sent_queue, message_key, message_value)
            await self.redis.hdel(self.to_send_queue, message_key)

            logger.info(
                f"Successfully processed message to chat {chat_id}, message {message_id}, content: {text}"
            )
            return True

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message key {message_key}: {e}")
        except KeyError as e:
            logger.error(f"Missing required field in message data: {e}")
        except Exception as e:
            logger.error(f"Failed to process message: {e}")

        return False

    async def process_queue(self) -> None:
        """Continuously process messages from queue"""
        while True:
            try:
                # Get all messages from queue
                messages = await self.redis.hgetall(self.to_send_queue)

                if not messages:
                    await asyncio.sleep(1)
                    continue

                for message_key_bytes, message_value_bytes in messages.items():
                    message_key = message_key_bytes.decode("utf-8")
                    message_value = message_value_bytes.decode("utf-8")

                    await self.process_message(message_key, message_value)

            except Exception as e:
                # logger.error(f"Error processing queue: {e}")
                await asyncio.sleep(5)


async def start_worker() -> None:
    """Initialize and start the worker"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Initialize dependencies
    # bot = Bot(token=bot_token)

    # Start worker
    # worker = MessageQueueWorker(redis_client=redis, bot=bot)
    worker = MessageQueueWorker()
    logger.info('starting licening')
    await worker.process_queue()


if __name__ == "__main__":
    asyncio.run(start_worker())

