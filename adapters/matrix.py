import asyncio
import logging
import os

from nio import AsyncClient, MatrixRoom, RoomMessageText
from nio.events.room_events import RoomMessageText
from typing import Dict, Callable

import config
from core.link import handle_matrix_links

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
        self._sync_task = None
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
        await handle_matrix_links(room, event, self.client)

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
        try:
            self._sync_task = asyncio.create_task(self.client.sync_forever(timeout=30000, full_state=True))
            await self._sync_task
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, shutting down...")
        except asyncio.CancelledError:
            logger.info("Sync loop cancelled, shutting down...")
        finally:
            await self.client.close()

    async def stop(self):
        """Stop the bot gracefully."""
        logger.info("Stopping Matrix bot...")
        try:
            if hasattr(self, '_sync_task') and not self._sync_task.done():
                self._sync_task.cancel()
                try:
                    await self._sync_task
                except asyncio.CancelledError:
                    pass
            # Close the client connection
            await self.client.close()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


# command handlers
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
    bot.add_command("help", help_command)

    # Start the bot with signal handling
    try:
        # Setup signal handlers for graceful shutdown
        import signal

        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            loop = asyncio.get_event_loop()
            loop.create_task(bot.stop())
            if not loop.is_running():
                return

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        await bot.start()
    except KeyboardInterrupt:
        logger.info("Shutdown signal received")
        await bot.stop()
    except Exception as e:
        logger.error(f"Bot error: {e}")
    finally:
        # Make sure to close the client connection on disconnect
        logger.info('Shutting down matrix bot...')
        await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())