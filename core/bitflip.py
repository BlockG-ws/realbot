from aiogram.types import Message

from config import config


def bitflip(text: str) -> str:
    """将文本中的0和1进行互换，遇到 0.x 就 1-0.x"""
    import re

    def replace_func(match):
        value = match.group()
        try:
            num = float(value)
            if 0 < num < 1:
                return str(1 - num)
            if num == 1.0:
                return str(0)
            if num == 0.0:
                return str(1)
            else:
                return value
        except ValueError:
            return value

    flipped_text = re.sub(r'\d*\.?\d+', replace_func, text)
    return flipped_text

async def handle_bitflip_command(message: Message) -> None:
    if not config.is_feature_enabled('bitflip', message.chat.id):
        return
    """获取回复的消息文本"""
    if not message.reply_to_message or not message.reply_to_message.text:
        await message.reply("请回复一条消息进行0/1翻转")
        return

    original_text = message.reply_to_message.text.replace("我","你").replace("窝","泥")
    if "0.5" in original_text:
        await message.reply_to_message.reply(f"确实，{original_text}")
        return
    flipped_text = bitflip(original_text)

    await message.reply_to_message.reply(f"错误的，{flipped_text}")