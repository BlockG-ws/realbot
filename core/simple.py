from aiogram import html
from aiogram.types import Message


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

async def dummy_handler(message: Message) -> None:
    """A handler to catch all other messages"""
    pass