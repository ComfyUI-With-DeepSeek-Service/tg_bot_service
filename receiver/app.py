import aiohttp
from aiogram import Dispatcher
from aiogram.types import Message
from aiogram_dialog import DialogManager
from loguru import logger


def setup_handlers(dp: Dispatcher):

    @dp.message()
    async def start(message: Message, dialog_manager: DialogManager):
        logger.info(f'Got message: {message.text}')

        request_data = {
            'chat_id': message.chat.id,
            'message_id': message.message_id,
            'prompt': message.text
        }
        async with aiohttp.ClientSession() as session:
            response = await session.post(
                url="backend:8888//make_text_request",  # TODO get url from env
                data=request_data
            )
            logger.info(f'Sent message with data: {request_data}\n Response: {response.json()}')
