import aiohttp
from aiogram import Dispatcher
from aiogram.types import Message
# from aiogram_dialog import DialogManager
from loguru import logger

from settings.config import settings


def setup_handlers(dp: Dispatcher):

    @dp.message()
    async def start(message: Message):
    # async def start(message: Message, dialog_manager: DialogManager):
        logger.info(f'Got message: {message.text}')

        request_data = {
            'chat_id': message.chat.id,
            'message_id': message.message_id,
            'prompt': f'Готовлю ответ на сообщение:\n\n{message.text}',
        }

        # TODO if exception happens - answer on message that there is problem with backend service immediately
        async with aiohttp.ClientSession() as session:  # TODO move session generator to init of class/fabric?
            response = await session.post(
                url=(
                    f'http://{settings.BACKEND_SERVICE_HOST}:{settings.BACKEND_SERVICE_PORT}'
                    f'/make_text_request'
                ),  # TODO move link generation to settings?
                json=request_data,
                headers={"Content-Type": "application/json"}  # TODO check if needed
            )
            response_data = await response.json()
            logger.info(f'Sent message with data: {request_data}\n\nGot answer: {response_data}')

    # TODO handle buttons (answer/chain of mind)
    # TODO handle image(s) + text message
    # TODO handle text answer
    # TODO handle image(s) + text answer
    # TODO handle model select
    # TODO handle select chat/generate mode
    # TODO handle params to run select
