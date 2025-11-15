from adapters.db.models import Lottery

async def save_lottery_info(chat_id: int, lottery_data: dict) -> int | None:
    """Save lottery information for a specific chat_id."""
    lottery_obj = await Lottery.create(chat_id=chat_id, type=lottery_data['type'], winner_count=lottery_data['number_of_winners'], max_participants=lottery_data.get('max_participants'),
                                       end_time=lottery_data.get('end_time'), title=lottery_data['title'],
                                       description=lottery_data.get('description'), participants=[], creator=lottery_data['creator'], token=lottery_data.get('token'),is_ended=False)
    await lottery_obj.save()
    return getattr(lottery_obj, 'id', None)

async def get_lottery_info(lottery_id: int, chat_id: None | int) -> dict:
    """Retrieve lottery information for a specific chat_id."""
    if chat_id is None:
        lotteries = await Lottery.filter(id=lottery_id).values()
    else:
        lotteries = await Lottery.filter(chat_id=chat_id, id=lottery_id).values()
    return lotteries[0] if lotteries else {}

async def get_all_unended_lotteries() -> list[dict]:
    """Retrieve all unended lotteries."""
    lotteries = await Lottery.filter(is_ended=False).values()
    return lotteries

async def update_lottery_info(chat_id: None | int, lottery_id: int,lottery_data: dict) -> None:
    """Update lottery information for a specific chat_id."""
    lottery = {}
    if chat_id is None:
        lottery = await Lottery.get_or_none(id=lottery_id)
    else:
        lottery = await Lottery.get_or_none(chat_id=chat_id,id=lottery_id)
    if lottery:
        for key, value in lottery_data.items():
            setattr(lottery, key, value)
        await lottery.save()

async def end_lottery(chat_id: int, lottery_id: int) -> None:
    """Mark the lottery as ended for a specific chat_id."""
    lottery = await Lottery.get_or_none(chat_id=chat_id, id=lottery_id)
    if lottery:
        lottery.is_ended = True
        await lottery.save()