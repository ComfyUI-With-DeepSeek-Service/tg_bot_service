from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import aiohttp
from aiogram import Dispatcher
from aiogram.types import Message
from pydantic import BaseModel, Field, HttpUrl, validator
from loguru import logger
from settings.config import settings


class RequestData(BaseModel):
    """
    Модель данных для запроса к бэкенд-сервису.

    :param chat_id: ID чата в Telegram
    :param message_id: ID сообщения в Telegram
    :param prompt: Текст запроса для обработки
    """
    chat_id: int = Field(..., description="ID чата в Telegram")
    message_id: int = Field(..., description="ID сообщения в Telegram")
    prompt: str = Field(..., description="Текст запроса для обработки")


class ResponseData(BaseModel):
    """
    Модель данных ответа от бэкенд-сервиса.

    :param status: Статус ответа
    :param message: Текст ответа
    :param additional_data: Дополнительные данные (опционально)
    """
    status: str = Field(..., description="Статус ответа")
    message: str = Field(..., description="Текст ответа")
    additional_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Дополнительные данные ответа"
    )


class BackendServiceConfig(BaseModel):
    """
    Конфигурация подключения к бэкенд-сервису.

    :param host: Хост бэкенд-сервиса
    :param port: Порт бэкенд-сервиса
    :param base_url: Базовый URL (автоматически генерируется из host и port)
    :param timeout: Таймаут подключения в секундах
    """
    host: str = Field(..., description="Хост бэкенд-сервиса")
    port: int = Field(..., description="Порт бэкенд-сервиса")
    base_url: HttpUrl = Field(..., description="Базовый URL бэкенд-сервиса")
    timeout: int = Field(30, description="Таймаут подключения в секундах")

    @validator('base_url', pre=True, always=True)
    def construct_base_url(cls, v, values):
        """Автоматически генерирует base_url из host и port."""
        if v is None:
            return f"http://{values['host']}:{values['port']}"
        return v


class IMessageHandler(ABC):
    """Абстрактный базовый класс для обработчиков сообщений."""

    @abstractmethod
    async def handle(self, message: Message) -> None:
        """
        Обрабатывает входящее сообщение.

        :param message: Входящее сообщение от пользователя
        :raises: NotImplementedError если метод не реализован
        """
        raise NotImplementedError


class BackendServiceClient:
    """Клиент для взаимодействия с бэкенд-сервисом."""

    def __init__(self, config: BackendServiceConfig, session: aiohttp.ClientSession):
        """
        Инициализация клиента.

        :param config: Конфигурация подключения
        :param session: Сессия aiohttp
        """
        self.config = config
        self.session = session

    async def make_text_request(self, request_data: RequestData) -> ResponseData:
        """
        Отправляет текстовый запрос к бэкенд-сервису.

        :param request_data: Данные запроса
        :return: Ответ от сервиса
        :raises: aiohttp.ClientError при ошибках сети
        :raises: ValueError при невалидных данных
        """
        url = f"{self.config.base_url}/make_text_request"

        try:
            async with self.session.post(
                    url=url,
                    json=request_data.dict(),
                    headers={"Content-Type": "application/json"},
                    timeout=self.config.timeout
            ) as response:
                response.raise_for_status()
                return ResponseData.parse_obj(await response.json())

        except aiohttp.ClientError as e:
            logger.error(f"Backend service error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise


class TextMessageHandler(IMessageHandler):
    """Обработчик текстовых сообщений."""

    def __init__(self, backend_client: BackendServiceClient):
        """
        Инициализация обработчика.

        :param backend_client: Клиент для работы с бэкенд-сервисом
        """
        self.backend_client = backend_client

    async def handle(self, message: Message) -> None:
        """
        Обрабатывает текстовое сообщение.

        :param message: Входящее текстовое сообщение
        :raises: Exception при ошибках обработки
        """
        logger.info(f'Got message: {message.text}')

        request_data = RequestData(
            chat_id=message.chat.id,
            message_id=message.message_id,
            prompt=f'Готовлю ответ на сообщение:\n\n{message.text}',
        )

        try:
            response = await self.backend_client.make_text_request(request_data)
            logger.info(
                f'Sent message with data: {request_data}\n\nGot answer: {response}'
            )
        except Exception as e:
            await message.answer("Произошла ошибка при обработке вашего запроса")
            logger.error(f"Error processing message: {e}")
            raise


class MessageHandlerFactory:
    """Фабрика для создания обработчиков сообщений."""

    @staticmethod
    async def create_text_handler() -> TextMessageHandler:
        """
        Создает обработчик текстовых сообщений.

        :return: Экземпляр TextMessageHandler
        """
        config = BackendServiceConfig(
            host=settings.BACKEND_SERVICE_HOST,
            port=settings.BACKEND_SERVICE_PORT
        )

        session = aiohttp.ClientSession()
        backend_client = BackendServiceClient(config, session)
        return TextMessageHandler(backend_client)


def setup_handlers(dp: Dispatcher) -> None:
    """
    Настраивает обработчики сообщений для бота.

    :param dp: Диспетчер aiogram
    """

    @dp.message()
    async def handle_message(message: Message) -> None:
        """
        Обрабатывает входящее сообщение.

        :param message: Входящее сообщение от пользователя
        """
        try:
            handler = await MessageHandlerFactory.create_text_handler()
            await handler.handle(message)
        except Exception as e:
            logger.error(f"Failed to process message: {e}")

