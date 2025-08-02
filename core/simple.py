import asyncio

from aiogram import html
from aiogram.types import Message

import config


async def handle_start_command(message: Message) -> None:
    """Handle /start command"""
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!")

async def handle_baka(message: Message) -> None:
    await message.reply(f"你是笨蛋")

async def handle_info_command(message: Message) -> None:
    """Handle /info command"""
    user = message.from_user
    chat = message.chat
    response = (
        f"User Info:\n"
        f"Name: {html.bold(user.full_name)}\n"
        f"Username: @{user.username if user.username else 'N/A'}\n"
        f"User ID: {user.id}\n\n"
        f"Chat Info:\n"
        f"Chat Title: {html.bold(chat.title)}\n"
        f"Chat ID: {chat.id}\n"
    )
    await message.reply(response)

async def handle_ping_command(message: Message) -> None:
    """Handle /ping command"""
    import time
    user_sent_time = message.date.timestamp()
    bot_time_now = time.time()
    time_diff = bot_time_now - user_sent_time
    response = f"Pong! Time taken: {round(time_diff * 1000, 2)} milliseconds"
    await message.reply(response)

async def handle_tips_command(message: Message) -> None:
    """Handle /tips command"""
    tips = [
        "你知道吗：其实 tips 都是废话（确信",
        "如果 bot 没有回复链接，说明链接不需要被清理",
        "不管如何，你今天都很棒！",
        "这个 bot 暂时还跑在一台运行着 Arch Linux 的笔电上",
        "/ping 命令其实显示的是 bot 到 Telegram 服务器的延迟，而不是用户到 bot 的延迟",
        "bot 的链接清理功能其实大多归功于 ➗ Actually Legitimate URL Shortener Tool 规则集",
        "bot 的功能可以被选择性的开启或者关闭，但是示例 bot 为了方便开发和测试，默认开启了所有功能",
        "说真的，你应该去看看 @kmuav2bot",
        "任何一条 tips 消息都会在一分钟后自动消失，再也不用担心消息堆积了",
    ]
    import random
    response = random.choice(tips)
    tips_message = await message.reply(response)
    # Delete the message after 1 minute
    await asyncio.sleep(60)
    await tips_message.delete()

async def handle_about_command(message: Message) -> None:
    """Handle /about command"""
    import time
    bot_time_start = time.time()
    about_message = await message.reply('Loading...')
    from dulwich.repo import Repo
    git_commit_hash = Repo('.').head().decode('utf-8')[:7]  # Get the first 7 characters of the commit hash
    response = f"realbot@g{git_commit_hash}\n\n"
    response += "孩子不懂随便写的 bot\n"
    if message.chat.id == config.config.get_admin_id():
        response += '\nDebug Info:\n'
        import os
        response += 'Python Version: ' + str(os.sys.version) + '\n'
        response += 'System Info: ' + '\n' + ' '.join(str(x) for x in os.uname()) + '\n'
    response += '\n这个命令比较慢，dulwich 负全责（小声），'
    bot_time_end = time.time()
    time_diff = bot_time_end - bot_time_start
    if time_diff < 1:
        response += f"也就大概花了 {round(time_diff * 1000, 2)} ms..."
    elif time_diff < 60:
        response += f"也就大概花了 {round(time_diff, 2)} 秒..."
    else:
        minutes = int(time_diff // 60)
        seconds = round(time_diff % 60, 2)
        response += f"也就大概花了 {minutes} 分 {seconds} 秒..."
    await about_message.edit_text(response)

async def dummy_handler(message: Message) -> None:
    """A handler to catch all other messages"""
    pass