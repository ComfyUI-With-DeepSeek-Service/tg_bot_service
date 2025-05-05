import asyncio
import json
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from aiogram import Bot
from loguru import logger
from pydantic import BaseModel, ValidationError
from redis.asyncio import Redis

from settings.config import settings


class MessageData(BaseModel):
    """
    Модель данных сообщения для валидации входных параметров.

    Attributes:
        chat_id: Идентификатор чата в Telegram
        message_id: Идентификатор сообщения в Telegram
    """
    chat_id: int
    message_id: int


class IMessageProcessor(ABC):
    """Абстрактный базовый класс для обработки сообщений"""

    @abstractmethod
    async def process_message(self, message_key: str, message_value: str) -> bool:
        """
        Обработка одного сообщения из очереди.

        :param message_key: Ключ сообщения в формате JSON
        :param message_value: Текст сообщения для отправки
        :return: Флаг успешности обработки
        :raises ValueError: При ошибках валидации данных
        :raises Exception: При ошибках отправки сообщения
        """
        pass


class RedisMessageQueueWorker:
    """
    Класс для работы с очередью сообщений в Redis.

    Обрабатывает сообщения из очереди, отправляет их через бота Telegram
    и перемещает в очередь отправленных сообщений.
    """

    def __init__(
            self,
            redis: Redis,
            bot: Bot,
            processor: IMessageProcessor,
            to_send_queue: str = settings.REDIS_ANSWER_QUEUE,
            sent_queue: str = settings.REDIS_SENT_QUEUE,
            poll_interval: int = 1,
            error_retry_interval: int = 5
    ) -> None:
        """
        Инициализация воркера.

        :param redis: Клиент Redis
        :param bot: Экземпляр бота Telegram
        :param processor: Обработчик сообщений
        :param to_send_queue: Название очереди для отправки
        :param sent_queue: Название очереди отправленных сообщений
        :param poll_interval: Интервал опроса очереди в секундах
        :param error_retry_interval: Интервал повтора при ошибках
        """
        self.redis = redis
        self.bot = bot
        self.processor = processor
        self.to_send_queue = to_send_queue
        self.sent_queue = sent_queue
        self.poll_interval = poll_interval
        self.error_retry_interval = error_retry_interval

    async def run(self) -> None:
        """
        Запуск обработки очереди сообщений.

        Бесконечно опрашивает очередь и обрабатывает сообщения.
        """
        logger.info('Starting message queue worker')

        while True:
            try:
                await self._process_available_messages()
            except Exception as e:
                logger.error(f"Error processing queue: {e}")
                await asyncio.sleep(self.error_retry_interval)

    async def _process_available_messages(self) -> None:
        """
        Обработка всех доступных сообщений в очереди.

        :raises Exception: При ошибках работы с Redis
        """
        messages = await self._get_messages_from_queue()

        if not messages:
            await asyncio.sleep(self.poll_interval)
            return

        for message_key_bytes, message_value_bytes in messages.items():
            message_key = message_key_bytes.decode("utf-8")
            message_value = message_value_bytes.decode("utf-8")

            await self.processor.process_message(message_key, message_value)

    async def _get_messages_from_queue(self) -> Dict[bytes, bytes]:
        """
        Получение всех сообщений из очереди.

        :return: Словарь сообщений (ключ: значение)
        :raises Exception: При ошибках работы с Redis
        """
        return await self.redis.hgetall(self.to_send_queue)


class TelegramMessageProcessor(IMessageProcessor):
    """
    Обработчик сообщений для Telegram.

    Отправляет сообщения через бота и управляет очередями в Redis.
    """

    def __init__(
            self,
            redis: Redis,
            bot: Bot,
            sent_queue: str = settings.REDIS_SENT_QUEUE,
            to_send_queue: str = settings.REDIS_ANSWER_QUEUE
    ) -> None:
        """
        Инициализация обработчика.

        :param redis: Клиент Redis
        :param bot: Экземпляр бота Telegram
        :param sent_queue: Название очереди отправленных сообщений
        :param to_send_queue: Название очереди для отправки
        """
        self.redis = redis
        self.bot = bot
        self.sent_queue = sent_queue
        self.to_send_queue = to_send_queue

    async def process_message(self, message_key: str, message_value: str) -> bool:
        """
        Обработка одного сообщения из очереди.

        :param message_key: Ключ сообщения в формате JSON
        :param message_value: Текст сообщения для отправки
        :return: Флаг успешности обработки
        :raises ValueError: При ошибках валидации данных
        :raises Exception: При ошибках отправки сообщения
        """
        logger.info(f'Processing message: {message_key}, value: {message_value}')

        try:
            message_data = self._parse_message_data(message_key)
            await self._send_telegram_message(message_data, message_value)
            await self._move_to_sent_queue(message_key, message_value)

            logger.info(
                f'Successfully processed message to chat {message_data.chat_id}, '
                f'message {message_data.message_id}, content: {message_value}'
            )
            return True

        except json.JSONDecodeError as e:
            logger.error(f'Failed to parse message key {message_key}: {e}')
        except ValidationError as e:
            logger.error(f'Invalid message data format: {e}')
        except KeyError as e:
            logger.error(f'Missing required field in message data: {e}')
        except Exception as e:
            logger.error(f'Failed to process message: {e}')

        return False

    def _parse_message_data(self, message_key: str) -> MessageData:
        """
        Парсинг и валидация данных сообщения.

        :param message_key: Ключ сообщения в формате JSON
        :return: Валидированные данные сообщения
        :raises json.JSONDecodeError: При ошибках парсинга JSON
        :raises ValidationError: При ошибках валидации данных
        """
        message_dict = json.loads(message_key)
        return MessageData(**message_dict)

    async def _send_telegram_message(
            self,
            message_data: MessageData,
            text: str
    ) -> None:
        """
        Отправка сообщения через бота Telegram.

        :param message_data: Данные сообщения
        :param text: Текст сообщения
        :raises Exception: При ошибках отправки сообщения
        """
        await self.bot.send_message(
            chat_id=message_data.chat_id,
            text=text,
            reply_to_message_id=message_data.message_id,
        )

    async def _move_to_sent_queue(self, message_key: str, message_value: str) -> None:
        """
        Перемещение сообщения в очередь отправленных.

        :param message_key: Ключ сообщения
        :param message_value: Значение сообщения
        :raises Exception: При ошибках работы с Redis
        """
        await self.redis.hset(self.sent_queue, message_key, message_value)
        await self.redis.hdel(self.to_send_queue, message_key)
