from typing import Callable, Dict, Awaitable, Any

from unidecode import unidecode

from aiogram import BaseMiddleware
from aiogram.types import Message

class AntiFakeChannelUsersMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self.counter = 0

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        linked_info = {}
        if event.chat.type == 'supergroup':
            from adapters.db.anti_fake_users import get_linked_channel_info, update_linked_channel_info
            linked_info = await get_linked_channel_info(event.chat.id)
            if event.sender_chat and event.is_automatic_forward:
                # 检测绑定频道消息是否有变动
                if linked_info['id'] != event.sender_chat.id or linked_info['fullname'] != event.sender_chat.full_name or linked_info['username'] != (event.sender_chat.username or ""):
                    fullname = normalize_channel_names(event.sender_chat.full_name)
                    username = event.sender_chat.username or ""
                    await update_linked_channel_info(event.chat.id, event.sender_chat.id, fullname, username)
            if not event.sender_chat or (not event.is_automatic_forward and not event.from_user.is_bot):
                # Message is sent by a linked channel
                normalized_fullname = normalize_channel_names(event.from_user.full_name)
                if normalized_fullname == linked_info['fullname']:
                    await handle_fake_channel_message(event)
        return await handler(event, data)

def normalize_channel_names(name: str) -> str:
    def is_cjk(character):
        # 判断字符是否为中日韩统一表意文字
        return '\u4e00' <= character <= '\u9fff'
    normalized = []
    for char in name:
        if is_cjk(char) or char.isascii():
            normalized.append(char)
        else:
            normalized.append(unidecode(char))
    return ''.join(normalized)

async def handle_fake_channel_message(message: Message) -> None:
    """处理疑似伪装频道用户的消息"""
    try:
        await message.bot.ban_chat_member(chat_id=message.chat.id, user_id=message.from_user.id)
        await message.delete()
    except Exception as err:
        await message.reply(f"发现疑似伪装频道的用户，但删除并封禁操作失败，请检查 bot 是否有相关权限。\n{str(err)}")