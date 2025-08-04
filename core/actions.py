from aiogram.types import Message

from config import config

import logging

async def handle_actions(message: Message) -> None:
    if not config.is_feature_enabled('actions', message.chat.id):
        logging.debug(f"收到了命中 / 开头的的消息，但是 actions 功能未启用，跳过处理")
        return
    rawtext = message.text
    logging.debug(f"收到了命中 / 开头的消息: {rawtext}")
    # 防止识别成命令而被误触发
    import re
    if re.match("^[a-zA-Z]+$", rawtext.replace('/','',1)) or '@' in rawtext:
        logging.debug(f"{rawtext} 看起来是一条命令，跳过处理")
        return

    from_user = message.from_user.mention_html(message.sender_chat.title) if message.sender_chat else message.from_user.mention_html()
    replied_user = message.reply_to_message.from_user.mention_html(message.reply_to_message.sender_chat.title) if message.reply_to_message and message.reply_to_message.sender_chat else (message.reply_to_message.from_user.mention_html() if message.reply_to_message else None)
    if " " in rawtext:
        if rawtext.split(" ")[0].replace('/','',1).isascii():
            return
        await message.reply(f"{from_user} {rawtext.split(" ")[0].replace('/','')}了 {replied_user if message.reply_to_message else '自己' } {''.join(rawtext.split(" ")[1:])}！",disable_web_page_preview=True)
    else:
        await message.reply(f"{from_user} {message.text.replace('/','')}了 {replied_user if message.reply_to_message else '自己'}！",disable_web_page_preview=True)

async def handle_reverse_actions(message: Message) -> None:
    from_user = message.from_user.mention_html(message.sender_chat.title) if message.sender_chat else message.from_user.mention_html()
    replied_user = message.reply_to_message.from_user.mention_html(message.reply_to_message.sender_chat.title) if message.reply_to_message and message.reply_to_message.sender_chat else message.reply_to_message.from_user.mention_html()
    if not config.is_feature_enabled('actions', message.chat.id):
        logging.debug(f"收到了命中 \\ 开头的的消息，但是 actions 功能未启用，跳过处理")
        return
    logging.debug(f"收到了命中 \\ 开头的消息: {message.text}")
    await message.reply(f"{from_user} 被 {replied_user if message.reply_to_message else '自己'} {message.text.replace('\\','')}了！",disable_web_page_preview=True)