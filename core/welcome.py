import logging

from aiogram.enums import ChatMemberStatus
from aiogram.types import ChatMemberUpdated

from config import config


async def get_welcome_message(chat_id: int) -> str | None:
    if chat_id is None:
        return None
    elif not await config.is_feature_enabled('welcome', chat_id):
        logging.debug(f"收到了欢迎事件，但是 welcome 功能未启用，跳过处理")
        return None
    # 根据 chat_id 获取不同的欢迎消息
    return await config.get_feature_config('welcome', chat_id)['message']


async def handle_tg_welcome(event: ChatMemberUpdated):
    """
    处理用户加入群组的事件，发送欢迎消息
    """
    try:
        if event.new_chat_member.status == ChatMemberStatus.MEMBER:
            welcome_message = await get_welcome_message(event.chat.id)
            if welcome_message:
                await event.answer(welcome_message)
    except Exception as e:
        logging.error(f"Error in handle_tg_welcome: {e}")