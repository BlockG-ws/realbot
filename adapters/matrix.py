import asyncio
import json
import logging
import os
import sys

from nio import AsyncClient, MatrixRoom, RoomMessageText
from nio.events.room_events import RoomMessageText
from typing import Dict, Callable

import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MatrixAdapter:
    def __init__(self, homeserver: str, user_id: str, token: str, device_name: str = "MatrixBot"):
        """
        Initialize the Matrix bot.

        Args:
            homeserver: The Matrix homeserver URL
            user_id: The bot's Matrix user ID
            token: The bot's token
            device_name: Device name for the bot
        """
        self.homeserver = homeserver
        self.user_id = user_id
        self.token = token
        self.device_name = device_name
        self.client = AsyncClient(homeserver, user_id)
        self.commands: Dict[str, Callable] = {}

        # Register event handlers
        self.client.add_event_callback(self.message_callback, RoomMessageText)

    def add_command(self, command: str, handler: Callable):
        """Add a command handler."""
        self.commands[command.lower()] = handler

    async def message_callback(self, room: MatrixRoom, event: RoomMessageText):
        """Handle incoming messages."""
        # Ignore messages from the bot itself
        if event.sender == self.user_id:
            return

        # Check if message starts with command prefix
        message = event.body.strip()
        if not message.startswith('!'):
            return

        # Parse command and arguments
        parts = message[1:].split(' ', 1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        # Execute command if it exists
        if command in self.commands:
            try:
                response = await self.commands[command](room, event, args)
                if response:
                    await self.send_message(room.room_id, response)
            except Exception as e:
                logger.error(f"Error executing command {command}: {e}")
                await self.send_message(room.room_id, f"Error executing command: {str(e)}")
        else:
            await self.send_message(room.room_id, f"Unknown command: {command}")

    async def send_message(self, room_id: str, message: str):
        """Send a message to a room."""
        await self.client.room_send(
            room_id=room_id,
            message_type="m.room.message",
            content={
                "msgtype": "m.text",
                "body": message
            }
        )

    async def start(self):
        """Start the bot."""
        logger.info("Starting Matrix bot...")

        # Login
        #response = await self.client.login(token=self.token, device_name=self.device_name)
        self.client.access_token = self.token
        self.client.device_id = "REALBOT"

        logger.info(f"Logged in as {self.user_id}")

        # Sync and listen for events
        await self.client.sync_forever(timeout=30000)

    async def stop(self):
        """Stop the bot."""
        logger.info("Stopping Matrix bot...")
        await self.client.close()


# Example command handlers
async def hello_command(room: MatrixRoom, event: RoomMessageText, args: str) -> str:
    """Handle !hello command."""
    return f"Hello {event.sender}!"


async def echo_command(room: MatrixRoom, event: RoomMessageText, args: str) -> str:
    """Handle !echo command."""
    if not args:
        return "Usage: !echo <message>"
    return f"Echo: {args}"


async def help_command(room: MatrixRoom, event: RoomMessageText, args: str) -> str:
    """Handle !help command."""
    help_text = """
Available commands:
- !hello - Say hello
- !echo <message> - Echo a message
- !help - Show this help message
    """
    return help_text.strip()


async def main():
    """Main function to run the bot."""
    # 从环境变量或配置文件中获取值
    matrix_config = config.Config().get_config_value('matrix', {})
    homeserver = matrix_config.get('homeserver', "https://matrix.org")
    user_id = matrix_config.get('user_id')
    token = os.getenv("MATRIX_BOT_TOKEN")

    # Create bot instance
    bot = MatrixAdapter(homeserver, user_id, token)

    # Register commands
    bot.add_command("hello", hello_command)
    bot.add_command("echo", echo_command)
    bot.add_command("help", help_command)

    try:
        print("Starting Matrix bot...")
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Bot interrupted by user")
        # TODO: fix unable to gracefully shutdown issue
        await bot.stop()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Bot error: {e}")
        await bot.stop()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())