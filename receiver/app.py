import aiohttp
from aiogram import Dispatcher
from aiogram.types import Message
from aiogram_dialog import DialogManager
from loguru import logger

from settings.config import settings


def setup_handlers(dp: Dispatcher):

    @dp.message()
    async def start(message: Message, dialog_manager: DialogManager):
        logger.info(f'Got message: {message.text}')

        request_data = {
            'chat_id': message.chat.id,
            'message_id': message.message_id,
            'prompt': f'Готовлю ответ на сообщение:\n\n{message.text}',
        }
        async with aiohttp.ClientSession() as session:
            response = await session.post(
                url=f'http://{settings.BACKEND_SERVICE_HOST}:{settings.BACKEND_SERVICE_PORT}/make_text_request',
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            response_data = await response.json()
            logger.info(f'Sent message with data: {request_data}\n\nGot answer: {response_data}')
