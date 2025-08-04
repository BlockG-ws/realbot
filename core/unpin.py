import logging

from aiogram.types import Message

from config import config


async def handle_unpin_channel_message(message: Message):
    """Handle unpinning messages from linked channels without a specific hashtag"""
    if not config.is_feature_enabled('unpin', message.chat.id):
        logging.debug('发现了频道试图置顶消息，但未启用 unpin 功能，跳过处理')
        return
    try:
        regex_pattern = config.get_feature_config('unpin', message.chat.id)['regex']
        # If a regex pattern exists, check if the message matches
        if regex_pattern:
            import re
            if re.search(regex_pattern, message.text or message.caption or ""):
                logging.debug(f"发现了频道试图置顶消息，但消息匹配了正则表达式{regex_pattern}，跳过取消置顶")
                # Message matches regex, don't unpin
                return
        # Either no regex pattern or message doesn't match, proceed to unpin
        logging.debug('正在尝试取消频道消息的置顶')
        await message.unpin()
    except Exception as e:
        logging.error('Error unpinning message:', e)