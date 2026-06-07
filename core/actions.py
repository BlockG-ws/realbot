import string

from aiogram.types import Message

from config import config

import logging

def _parse_action(parts: list[str], default_ending: str = "了") -> tuple[str, str, str | None, str]:
    """解析动作参数，支持 -r（替换后缀）和 -p（替换标点）。

    -r：无参数删除默认后缀，有参数将默认后缀替换为参数。
    -p：无参数删除标点，有参数将默认标点替换为参数。

    Returns:
        (to_remove, replace_with, punctuation, content)
        punctuation: None=默认"！",""=无标点，其他=自定义标点
    """
    # 分离 -r 和 -p 部分
    p_args = []
    has_p = "-p" in parts
    if has_p:
        p_idx = parts.index("-p")
        p_args = parts[p_idx + 1:]
        parts = parts[:p_idx]

    r_args = []
    if "-r" in parts:
        r_idx = parts.index("-r")
        content = " ".join(parts[:r_idx])
        r_args = parts[r_idx + 1:]
    else:
        content = " ".join(parts)

    # 处理 -r
    if "-r" not in parts:
        to_remove = ""
        replace_with = default_ending
    elif not r_args:
        to_remove = default_ending
        replace_with = ""
    else:
        to_remove = default_ending
        replace_with = " ".join(r_args)

    # 处理 -p
    if not has_p:
        punctuation = None
    elif not p_args:
        punctuation = ""
    else:
        punctuation = " ".join(p_args)

    return (to_remove, replace_with, punctuation, content)


async def handle_actions(message: Message) -> None:
    if not await config.is_feature_enabled('actions', message.chat.id):
        logging.debug(f"收到了命中 / 开头的的消息，但是 actions 功能未启用，跳过处理")
        return
    rawtext = message.text
    logging.debug(f"收到了命中 / 开头的消息")
    # 如果消息是 / 开头的，但是后续没有有意义的内容，则不处理
    if len(rawtext.replace('/','')) == 0 or all(char in string.punctuation for char in rawtext.replace('/','')):
        return
    # 防止识别成命令而被误触发
    import re
    if re.match("^[a-zA-Z]+$", rawtext.replace('/','',1)) or '@' in rawtext:
        logging.debug(f"{rawtext} 看起来是一条命令，跳过处理")
        return

    from_user = message.from_user.mention_html(message.sender_chat.title) if message.sender_chat else message.from_user.mention_html()
    replied_user = message.reply_to_message.from_user.mention_html(message.reply_to_message.sender_chat.title) if message.reply_to_message and message.reply_to_message.sender_chat else (message.reply_to_message.from_user.mention_html() if message.reply_to_message and message.reply_to_message.from_user else None)
    if " " in rawtext:
        parts = rawtext.split(" ")
        if parts[0].replace('/','',1).isascii():
            return
        verb = parts[0].replace('/', '')
        args = parts[1:]
        to_remove, replace_with, punctuation, content = _parse_action(args)
        verb = verb.removesuffix(to_remove) + replace_with
        punc = "！" if punctuation is None else punctuation
        if content:
            await message.reply(f"{from_user} {verb} {replied_user if message.reply_to_message and replied_user != from_user else '自己'} {content}{punc}", disable_web_page_preview=True)
        else:
            await message.reply(f"{from_user} {verb} {replied_user if message.reply_to_message and replied_user != from_user else '自己'}{punc}", disable_web_page_preview=True)
    else:
        await message.reply(f"{from_user} {message.text.replace('/','')}了 {replied_user if message.reply_to_message and replied_user != from_user else '自己'}！",disable_web_page_preview=True)

async def handle_reverse_actions(message: Message) -> None:
    from_user = message.from_user.mention_html(message.sender_chat.title) if message.sender_chat else message.from_user.mention_html()
    replied_user = message.reply_to_message.from_user.mention_html(message.reply_to_message.sender_chat.title) if message.reply_to_message and message.reply_to_message.sender_chat else (message.reply_to_message.from_user.mention_html() if message.reply_to_message and message.reply_to_message.from_user else None)
    if not await config.is_feature_enabled('actions', message.chat.id):
        logging.debug(f"收到了命中 \\ 开头的的消息，但是 actions 功能未启用，跳过处理")
        return
    logging.debug(f"收到了命中 \\ 开头的消息: {message.text}")
    rawtext = message.text
    if " " in rawtext:
        parts = rawtext.split(" ")
        verb = parts[0].replace('\\', '')
        args = parts[1:]
        to_remove, replace_with, punctuation, content = _parse_action(args)
        verb = verb.removesuffix(to_remove) + replace_with
        punc = "！" if punctuation is None else punctuation
        if content:
            await message.reply(f"{from_user} 被 {replied_user if message.reply_to_message and replied_user != from_user else '自己'} {verb} {content}{punc}", disable_web_page_preview=True)
        else:
            await message.reply(f"{from_user} 被 {replied_user if message.reply_to_message and replied_user != from_user else '自己'} {verb}{punc}", disable_web_page_preview=True)
    else:
        await message.reply(f"{from_user} 被 {replied_user if message.reply_to_message and replied_user != from_user else '自己'} {message.text.replace('\\','')}了！",disable_web_page_preview=True)