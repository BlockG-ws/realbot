from apscheduler.schedulers.background import BackgroundScheduler

from core.lottery import handle_draw_lottery

from adapters.scheduler.core import Scheduler
from zoneinfo import ZoneInfo
from datetime import datetime

bot = Scheduler.bot()

async def start_lottery_job(lottery_id: int, chat_id: int) -> None:
    """Start a lottery job."""
    from adapters.db.lottery import get_lottery_info
    lottery_info = await get_lottery_info(lottery_id, chat_id)
    scheduler = Scheduler.scheduler

    tz = ZoneInfo("Asia/Shanghai")
    end_time = lottery_info['end_time']
    if isinstance(end_time, str):
        end_time = datetime.fromisoformat(end_time)
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=tz)
    else:
        end_time = end_time.astimezone(tz)

    scheduler.add_job(
        func=handle_draw_lottery,
        trigger='date',
        run_date=end_time,
        args=[bot, lottery_id, chat_id],
        id=f'lottery_{lottery_id}_end',
        executor='default'
    )

async def recover_lottery_jobs() -> None:
    """Recover lottery jobs on startup."""
    from adapters.db.lottery import get_all_unended_lotteries
    lotteries = await get_all_unended_lotteries()
    scheduler = Scheduler.scheduler
    for lottery in lotteries:
        # Skip lotteries without end_time
        if not lottery.get('end_time'):
            continue
        lottery_id = lottery['id']
        chat_id = lottery['chat_id']
        end_time = lottery['end_time']
        tz = ZoneInfo("Asia/Shanghai")
        if isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time)
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=tz)
        else:
            end_time = end_time.astimezone(tz)
        now = datetime.now(tz=tz)
        if end_time > now:
            scheduler.add_job(
                func=handle_draw_lottery,
                trigger='date',
                run_date=end_time,
                args=[bot, lottery_id, chat_id],
                id=f'lottery_{lottery_id}_end',
                executor='default'
            )