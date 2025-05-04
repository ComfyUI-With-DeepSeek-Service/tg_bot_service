# check for redis updates, send to sender msg
import asyncio
import json

from aiogram import Bot
from loguru import logger
from redis.asyncio import Redis

from settings.config import settings


class MessageQueueWorker:
    def __init__(self, redis: Redis, tg_bot: Bot) -> None:
        self.redis = redis
        self.bot = tg_bot
        self.sent_queue = settings.REDIS_SENT_QUEUE
        self.to_send_queue = settings.REDIS_ANSWER_QUEUE

    async def process_answer_on_message(self, message_key: str, message_value: str) -> bool:
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
            chat_id = message_data['chat_id']
            message_id = message_data['message_id']
            text = message_value

            # Send message
            await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_to_message_id=message_id,
            )

            # Move to sent queue
            await self.redis.hset(self.sent_queue, message_key, message_value)
            await self.redis.hdel(self.to_send_queue, message_key)

            logger.info(
                f'Successfully processed message to chat {chat_id}, message {message_id}, content: {text}'
            )
            return True

        except json.JSONDecodeError as e:
            logger.error(f'Failed to parse message key {message_key}: {e}')
        except KeyError as e:
            logger.error(f'Missing required field in message data: {e}')
        except Exception as e:
            logger.error(f'Failed to process message: {e}')

        return False

    async def process_queue(self) -> None:
        """Continuously process messages from queue"""
        logger.info('Starting listening')

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

                    await self.process_answer_on_message(message_key=message_key, message_value=message_value)

            except Exception as e:
                logger.error(f"Error processing queue: {e}")
                await asyncio.sleep(5)
