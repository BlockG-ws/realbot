import asyncio

from aiogram import html
from aiogram.enums import ParseMode
from aiogram.types import Message
from chinese_calendar import is_workday

from config import config


async def handle_start_command(message: Message) -> None:
    """Handle /start command"""
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!")

async def handle_baka(message: Message) -> None:
    await message.reply(f"你是笨蛋")

async def handle_info_command(message: Message) -> None:
    """Handle /info command"""
    verbose = "verbose" in (message.text or "")
    # TODO: verbose mode
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
        "/ping 命令其实显示的是 bot 到 Telegram 服务器的延迟，而不是用户到 bot 的延迟",
        "bot 的链接清理功能其实大多归功于 ➗ Actually Legitimate URL Shortener Tool 规则集",
        "bot 的功能可以被选择性的开启或者关闭，但是示例 bot 为了方便开发和测试，默认开启了所有功能",
        "说真的，你应该去看看 @kmuav2bot",
        "任何一条 tips 消息都会在一分钟后自动消失，再也不用担心消息堆积了",
        "/mc 命令使用了 mcstatus 库来查询 Minecraft 服务器状态，而这个库曾经由 Dinnerbone 维护",
        "如果你找到了链接转换的问题，欢迎把它通过 <code>/report_broken_links 链接 需要去除的参数等等</code> 报告给开发者！"
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
    try:
        from dulwich.repo import Repo
        git_commit_hash = f"g{Repo('.').head().decode('utf-8')[:7]}"  # Get the first 7 characters of the commit hash
    except Exception:
        git_commit_hash = 'v20261016'  # Fallback when git operations fail
    response = f"realbot@{git_commit_hash}\n\n"
    response += "孩子不懂随便写的 bot\n"
    if message.chat.id == config.get_admin_id():
        response += '\nDebug Info:\n'
        import os
        response += 'Python Version: ' + str(os.sys.version) + '\n'
        response += 'System Info: ' + '\n' + ' '.join(str(x) for x in os.uname()) + '\n'
    response += '\n此 bot 以 GNU General Public License 3.0 及以上版本<a href="https://github.com/BlockG-ws/realbot">开源</a>。'
    await about_message.edit_text(response,disable_web_page_preview=True)

async def handle_nexusmods_id(message: Message) -> None:
    """输入n网尾号xxxx之后主动返回星露谷物语的对应mod"""
    nexusmods_id = message.text.replace(" ","").replace("N网尾号","").replace("n网尾号","")
    await message.reply(f"https://www.nexusmods.com/stardewvalley/mods/{nexusmods_id}")

async def handle_ds_command(message: Message) -> None:
    """判断当前是“梁文峰”还是梁文谷"""
    from datetime import datetime,time
    from zoneinfo import ZoneInfo
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    if is_workday(now.date()) and (time(9,0) <= now.time() < time(12,0) or time(14,0) <= now.time() < time(18,0)):
        await message.reply("现在是**梁文峰**",parse_mode=ParseMode.MARKDOWN_V2)
    else:
        await message.reply("现在是**梁文谷**",parse_mode=ParseMode.MARKDOWN_V2)
async def dummy_handler(message: Message) -> None:
    """A handler to catch all other messages"""
    pass