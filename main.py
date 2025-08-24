import asyncio
import logging
import signal
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
        # Setup signal handler for graceful shutdown
        def signal_handler(signum, frame):
            logging.info("Received shutdown signal, cancelling all tasks...")
            for task in tasks:
                task.cancel()

        # Register signal handlers
        for sig in (signal.SIGTERM, signal.SIGINT):
            asyncio.get_event_loop().add_signal_handler(sig, signal_handler, sig, None)

        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except asyncio.CancelledError:
            logging.info("All tasks cancelled successfully")
    else:
        logging.error("No bot is configured to start. Please check your configuration.")


if __name__ == "__main__":
    asyncio.run(main())