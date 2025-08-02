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

from core.post_to_fedi import router as fedi_router

from core.bitflip import handle_bitflip_command
from core.link import handle_links
from core.post_to_fedi import handle_auth, handle_post_to_fedi
from core.promote import handle_promote_command
from core.repeater import MessageRepeater
from core.report_links import report_broken_links
from core.simple import handle_start_command, handle_baka, dummy_handler, handle_info_command, handle_ping_command, \
    handle_tips_command
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
        actions_router = Router()
        repeater_router = Router()
        dummy_router = Router()

        # Register handlers on router
        router.message(CommandStart())(handle_start_command)
        router.message(Command('info'))(handle_info_command)
        router.message(Command('ping'))(handle_ping_command)
        router.message(Command('tips'))(handle_tips_command)
        # bitflip 模块
        router.message(Command('bitflip'))(handle_bitflip_command)
        # promote 模块
        router.message(Command('t'))(handle_promote_command)
        # stats 模块
        router.message(Command('stats'))(handle_stats_command)
        # fedi 模块
        router.message(Command('fauth'))(handle_auth)
        router.message(Command('post'))(handle_post_to_fedi)
        # link 模块
        router.message(Command('report_broken_links'))(report_broken_links)
        router.message(F.text.contains('http') & ~F.text.contains('/report_broken_links'))(handle_links)
        # unpin 模块
        # 不知道为什么检测不到频道的消息被置顶这个事件，暂时认为所有的频道消息都是被置顶的
        router.message(F.chat.type.in_({'group', 'supergroup'}) & F.sender_chat & (
                    F.sender_chat.type == 'channel') & F.is_automatic_forward)(
            handle_unpin_channel_message)
        # repeater 模块
        repeater_router.message(F.chat.type.in_({'group', 'supergroup'}))(MessageRepeater().handle_message)
        router.message(F.text == '我是笨蛋')(handle_baka)
        # 捕获所有其他消息
        dummy_router.message(F.chat.type.in_({'group', 'supergroup'}))(dummy_handler)

        # actions 模块
        actions_router.message(F.chat.type.in_({'group', 'supergroup'}) & F.text.startswith('/'))(handle_actions)
        actions_router.message(F.chat.type.in_({'group', 'supergroup'}) & F.text.startswith('\\'))(handle_reverse_actions)

        # Include router in dispatcher
        # 通用的路由
        self.dp.include_router(router)
        self.dp.include_router(actions_router)
        # 处理联邦宇宙认证相关
        self.dp.include_router(fedi_router)
        self.dp.include_router(repeater_router)
        self.dp.include_router(dummy_router)

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