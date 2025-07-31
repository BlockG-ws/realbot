import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram import F

from core.bitflip import handle_bitflip_command
from core.link import handle_links
from core.promote import handle_promote_command
from core.repeater import MessageRepeater
from core.simple import handle_start_command, handle_baka, dummy_handler, handle_info_command
from core.actions import handle_actions, handle_reverse_actions
from core.stats import handle_stats_command
from core.middleware.stats import MessageStatsMiddleware
from core.unpin import handle_unpin_channel_message

TOKEN = getenv("BOT_TOKEN")


class TelegramAdapter:
    def __init__(self):
        self.dp = Dispatcher()
        self.stats_middleware = MessageStatsMiddleware()
        self._setup_middleware()
        self._setup_handlers()

    def _setup_handlers(self):
        """Register handlers with core module functions"""
        # Create router
        router = Router()

        # Register handlers on router
        router.message(CommandStart())(handle_start_command)
        router.message(Command('info'))(handle_info_command)
        # bitflip 模块
        router.message(Command('bitflip'))(handle_bitflip_command)
        # promote 模块
        router.message(Command('t'))(handle_promote_command)
        # stats 模块
        router.message(Command('stats'))(handle_stats_command)
        # unpin 模块
        # 不知道为什么检测不到频道的消息被置顶这个事件，暂时认为所有的频道消息都是被置顶的
        router.message(F.chat.type.in_({'group', 'supergroup'}) & F.sender_chat & (
                    F.sender_chat.type == 'channel') & F.is_automatic_forward)(
            handle_unpin_channel_message)
        # actions 模块
        router.message(F.text.startswith('/'))(handle_actions)
        router.message(F.text.startswith('\\'))(handle_reverse_actions)
        router.message(F.text == '我是笨蛋')(handle_baka)
        # link 模块
        router.message(F.text.contains('http'))(handle_links)
        # repeater 模块
        router.message(F.chat.type.in_({'group', 'supergroup'}))(MessageRepeater().handle_message)

        # 捕获所有其他消息
        router.message(F.chat.type.in_({'group', 'supergroup'}))(dummy_handler)

        # Include router in dispatcher
        self.dp.include_router(router)

    def _setup_middleware(self):
        """注册中间件"""
        self.dp.message.middleware(self.stats_middleware)


    async def start(self):
        """Start the Telegram bot"""
        session = None
        if getenv("HTTPS_PROXY"):
            session = AiohttpSession(proxy=getenv("HTTPS_PROXY"))

        bot = Bot(
            token=TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
            session=session
        )

        await self.dp.start_polling(bot)


async def main() -> None:
    adapter = TelegramAdapter()
    await adapter.start()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())