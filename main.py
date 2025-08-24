import asyncio
import logging
import sys

import config
from adapters.tg import TelegramAdapter


async def main():
    """Main entry point"""
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

    tasks = []
    # Initialize and start Telegram adapter
    if config.Config().get_config_value('start_telegram_bot', True):
        tg_adapter = TelegramAdapter()
        tasks.append(tg_adapter.start())
    if config.Config().get_config_value('also_start_matrix_bot', False):
        import adapters.matrix as matrix_bot
        # Initialize and start Matrix bot if configured
        tasks.append(matrix_bot.main())
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
    else:
        logging.error("No bot is configured to start. Please check your configuration.")


if __name__ == "__main__":
    asyncio.run(main())