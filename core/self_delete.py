import logging

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message


async def handle_self_delete(message: Message):
    """让触发的消息能够被触发着和管理员删除"""
    bot = message.bot

    if message.reply_to_message and message.reply_to_message.from_user.id == bot.id:
        await message.reply_to_message.delete()
        admins = await bot.get_chat_administrators(message.reply_to_message.chat.id)
        # 提取所有有删除消息权限的管理员的 user_id
        admin_ids = [admin.user.id for admin in admins if admin.status == 'creator' or getattr(admin, "can_delete_messages", False)]
        if bot.id in admin_ids:
            try:
                await message.delete()
                return
            except TelegramBadRequest as e:
                return