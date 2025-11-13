from apscheduler.schedulers.asyncio import AsyncIOScheduler
from adapters.db.lottery import get_all_unended_lotteries


async def get_all_unended_jobs() -> list[dict]:
    """Retrieve all unended jobs from the database."""
    lottery_jobs = await get_all_unended_lotteries()
    return lottery_jobs

async def recover_jobs() -> None:
    """Recover jobs on startup."""
    if await get_all_unended_jobs():
        from adapters.scheduler.lottery import recover_lottery_jobs
        await recover_lottery_jobs()


class Scheduler:
    scheduler = AsyncIOScheduler()
    _bot = None

    @classmethod
    def get_bot(cls):
        """Lazily import TelegramAdapter to avoid circular imports and return the bot."""
        if cls._bot is None:
            from adapters.tg import TelegramAdapter
            cls._bot = TelegramAdapter.bot
        return cls._bot

    @classmethod
    def bot(cls):
        """Property accessor for bot."""
        return cls.get_bot()

    def start(self):
        """Start the scheduler."""
        self.scheduler.start()

