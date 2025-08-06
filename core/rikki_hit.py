from aiogram.types import Message
from core.middleware.rikki import RikkiMiddleware

async def handle_query_hit_command(message: Message) -> None:
    hit_status = RikkiMiddleware().get_user_status("5545347637")
    await message.reply(hit_status)