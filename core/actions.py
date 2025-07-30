from aiogram.types import Message

from config import config


async def handle_actions(message: Message) -> None:
    if not config.is_feature_enabled('actions', message.chat.id):
        return
    rawtext = message.text
    # 防止识别成命令而被误触发
    if rawtext.replace('/','',1).isalpha() or '@' in rawtext:
        return
    elif " " in message.text:
        if rawtext.split(" ")[0].replace('/','',1).isalpha():
            return
        await message.reply(f"{message.from_user.mention_html()} {rawtext.split(" ")[0].replace('/','')}了 {message.reply_to_message.from_user.mention_html() if message.reply_to_message else '自己' } {''.join(rawtext.split(" ")[1:])}！",disable_web_page_preview=True)
    else:
        await message.reply(f"{message.from_user.mention_html()} {message.text.replace('/','')}了 {message.reply_to_message.from_user.mention_html() if message.reply_to_message else '自己'}！",disable_web_page_preview=True)

async def handle_reverse_actions(message: Message) -> None:
    if not config.is_feature_enabled('actions', message.chat.id):
        return
    await message.reply(f"{message.from_user.mention_html()} 被 {message.reply_to_message.from_user.mention_html()} {message.text.replace('\\','')}了！",disable_web_page_preview=True)