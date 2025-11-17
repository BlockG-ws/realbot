import logging

from aiogram.types import Message

async def handle_whitelist_command(message: Message):
    """处理白名单命令"""
    chat_id = message.chat.id
    try:
        channel_id = int(message.text.split(' ')[1])
    except (IndexError, ValueError):
        await message.reply("请提供有效的频道ID")
        return
    member = await message.chat.get_member(message.from_user.id)
    if not member.status in ['administrator', 'creator']:
        await message.reply("只有管理员才能使用此命令")
        return
    from adapters.db.anti_fake_users import add_whitelist, get_whitelist
    whitelisted_channels = await get_whitelist(chat_id)
    if channel_id not in whitelisted_channels:
        await add_whitelist(message.chat.id, channel_id)
        await message.reply(f"已将频道 {channel_id} 添加到白名单")

async def handle_remove_whitelist_command(message: Message):
    """处理移除白名单命令"""
    chat_id = message.chat.id
    try:
        channel_id = int(message.text.split(' ')[1])
    except (IndexError, ValueError):
        await message.reply("请提供有效的频道ID")
        return
    member = await message.chat.get_member(message.from_user.id)
    if not member.status in ['administrator', 'creator']:
        await message.reply("只有管理员才能使用此命令")
        return
    from adapters.db.anti_fake_users import remove_whitelist, get_whitelist
    whitelisted_channels = await get_whitelist(chat_id)
    if channel_id in whitelisted_channels:
        await remove_whitelist(message.chat.id, channel_id)
        await message.reply(f"已将频道 {channel_id} 从白名单中移除")

async def handle_anonymous_channel_msgs(message: Message):
    """处理来自匿名频道的消息"""
    chat_id = message.chat.id
    channel_id = message.sender_chat.id if message.sender_chat else None
    is_from_binded_channel = message.is_automatic_forward
    from adapters.db.anti_fake_users import get_whitelist, get_ban_config
    whitelist = await get_whitelist(chat_id)
    also_ban = await get_ban_config(chat_id)
    if channel_id and channel_id not in whitelist and not is_from_binded_channel:
        try:
            if also_ban:
                await message.bot.ban_chat_member(chat_id, channel_id)
            else:
                await message.delete()
        except Exception as e:
            logging.warning("无法删除频道马甲消息，可能是因为没有权限",e)