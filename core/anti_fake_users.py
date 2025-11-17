import logging

from aiogram.types import Message

from config import config

async def handle_channel_manage_command(message: Message):
    """封禁频道马甲命令"""
    chat_id = message.chat.id
    if await config.is_feature_enabled('anti_anonymous', chat_id) is False:
        return
    cargs = message.text.split(' ')
    if len(cargs) < 2:
        await message.reply("用法： /fake [ban|unban|allow|disallow] 目标频道ID\n /fake auto_ban_channel [on|off]")
        return
    operation = cargs[1].lower()
    member = await message.chat.get_member(message.from_user.id)
    is_group_anonymous_admin = message.sender_chat and message.sender_chat.id == message.chat.id
    is_group_admin = member.status in ['administrator', 'creator'] or is_group_anonymous_admin
    if operation in ['ban', 'unban', 'allow', 'disallow']:
        from adapters.db.anti_fake_users import get_whitelist, add_whitelist, remove_whitelist
        whitelist = await get_whitelist(chat_id)
        if len(cargs) < 3:
            await message.reply(f"用法： /fake {operation} 目标频道ID")
            return
        try:
            channel_id = int(cargs[2])
            if not str(channel_id).startswith("-100"):
                raise ValueError("频道ID应为-100开头的整数")
        except (IndexError, ValueError):
            await message.reply("请提供有效的 bot api 格式的频道ID")
            return
        if not is_group_admin:
            await message.reply("只有管理员才能使用此命令")
            return
        if operation == 'ban':
            try:
                await message.bot.ban_chat_sender_chat(chat_id, channel_id)
                await message.reply(f"已封禁频道马甲 {channel_id}")
                return
            except Exception as e:
                logging.warning("无法封禁频道马甲，可能是因为没有权限",e)
                await message.reply(f"无法封禁频道马甲 {channel_id}，请检查权限")
        elif operation == 'unban':
            try:
                await message.bot.unban_chat_sender_chat(chat_id, channel_id)
                await message.reply(f"已解封频道马甲 {channel_id}")
                return
            except Exception as e:
                logging.warning("无法解封频道马甲，可能是因为没有权限",e)
                await message.reply(f"无法解封频道马甲 {channel_id}，请检查权限")
        elif operation == 'allow':
            if channel_id in whitelist:
                await message.reply(f"频道马甲 {channel_id} 已在白名单中")
                return
            await add_whitelist(chat_id, channel_id)
            await message.reply(f"已将频道马甲 {channel_id} 加入白名单")
        elif operation == 'disallow':
            if channel_id not in whitelist:
                await message.reply(f"频道马甲 {channel_id} 不在白名单中，无法移除")
                return
            await remove_whitelist(chat_id, channel_id)
            await message.reply(f"已将频道马甲 {channel_id} 移出白名单")
            return
    elif operation == 'auto_ban_channel':
        if is_group_admin:
            await message.reply("只有管理员才能使用此命令")
            return
        if len(cargs) < 3:
            await message.reply("用法： /fake auto_ban_channel [on|off]")
            return
        setting = cargs[2].lower()
        from adapters.db.anti_fake_users import set_ban_config
        if setting in ['on', 'true', '1', 'yes']:
            await set_ban_config(chat_id, True)
            await message.reply("已启用自动封禁频道马甲，当不在白名单的匿名频道发送消息时，会自动删除并且封禁该频道马甲")
        elif setting in ['off', 'false', '0', 'no']:
            await set_ban_config(chat_id, False)
            await message.reply("已禁用自动封禁频道马甲")
        else:
            await message.reply("用法： /fake auto_ban_channel [on|off]")

async def handle_anonymous_channel_msgs(message: Message):
    """处理来自匿名频道的消息"""
    chat_id = message.chat.id
    if config.is_feature_enabled('anti_anonymous', chat_id) is False:
        return
    channel_id = message.sender_chat.id if message.sender_chat else None
    is_from_binded_channel = message.is_automatic_forward
    is_group_anonymous_admin = message.sender_chat and message.sender_chat.id == message.chat.id
    from adapters.db.anti_fake_users import get_whitelist, get_ban_config
    whitelist = await get_whitelist(chat_id)
    also_ban = await get_ban_config(chat_id)
    if channel_id and channel_id not in whitelist and not is_from_binded_channel and is_group_anonymous_admin:
        try:
            if also_ban:
                await message.bot.ban_chat_sender_chat(chat_id, channel_id)
            else:
                await message.delete()
        except Exception as e:
            logging.warning("无法删除频道马甲消息，可能是因为没有权限",e)