import asyncio
import logging
import sys

from adapters.tg import TelegramAdapter


async def main():
    """Main entry point"""
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

    # Initialize and start Telegram adapter
    tg_adapter = TelegramAdapter()
    await tg_adapter.start()


if __name__ == "__main__":
    asyncio.run(main())