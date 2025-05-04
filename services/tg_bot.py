from aiogram import Bot
from loguru import logger

from settings.config import settings

logger.debug(f'Init tg bot')

tg_bot = Bot(token=settings.TELEGRAM_BOT_TOKEN.get_secret_value())
