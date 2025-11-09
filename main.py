import asyncio
import logging
import signal
import sys
from asyncio import TaskGroup

import adapters.db.core
import config
from adapters.tg import TelegramAdapter


async def main():
    """Main entry point"""
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

    tasks = []
    cfg = config.Config()
    # Initialize database
    await adapters.db.core.init_db()
    # Initialize and start Telegram adapter
    if cfg.get_config_value('start_telegram_bot', True):
        tg_adapter = TelegramAdapter()
        tasks.append(tg_adapter.start())
    if cfg.get_config_value('also_start_matrix_bot', False):
        import adapters.matrix as matrix_bot
        # Initialize and start Matrix bot if configured
        tasks.append(matrix_bot.main())
    running_tasks = []
    if tasks:
        try:
            async with TaskGroup() as group:
                for coro in tasks:
                    task = group.create_task(coro)
                    running_tasks.append(task)
        except asyncio.CancelledError:
            logging.info("All tasks cancelled successfully")
        finally:
            for task in running_tasks:
                task.cancel()
            logging.info("All tasks cancelled successfully, closing database connection.")
            await adapters.db.core.close_db()
            logging.info("All tasks finished successfully. Exiting.")
    else:
        logging.error("No bot is configured to start. Please check your configuration.")


if __name__ == "__main__":
    asyncio.run(main())