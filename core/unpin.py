from aiogram.types import Message

from config import config


async def handle_unpin_channel_message(message: Message):
    """Handle unpinning messages from linked channels without a specific hashtag"""
    if not config.is_feature_enabled('unpin', message.chat.id):
        return
    try:
        regex_pattern = config.get_feature_config('unpin', message.chat.id)['regex']
        print(regex_pattern)
        # If a regex pattern exists, check if the message matches
        if regex_pattern:
            import re
            if re.search(regex_pattern, message.text or message.caption or ""):
                # Message matches regex, don't unpin
                return
        # Either no regex pattern or message doesn't match, proceed to unpin
        print("trying to unpin the message")
        await message.unpin()
    except Exception as e:
        print('Error unpinning message:', e)