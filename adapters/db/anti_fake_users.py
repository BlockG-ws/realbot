from adapters.db.models import ChannelWhiteList

async def get_whitelist(chat_id: int) -> dict:
    """Retrieve whitelist for a specific chat_id."""
    whitelist = await ChannelWhiteList.get_or_none(chat_id=chat_id).values()
    return whitelist['whitelist'] if whitelist else []

async def add_whitelist(chat_id: int, channel: int) -> None:
    """Update whitelist for a specific chat_id."""
    data, created = await ChannelWhiteList.get_or_create(chat_id=chat_id)
    data.whitelist.append(channel)
    await data.save()

async def remove_whitelist(chat_id: int, channel: int) -> None:
    """Remove a channel from whitelist for a specific chat_id."""
    data = await ChannelWhiteList.get_or_none(chat_id=chat_id)
    if data and channel in data.whitelist:
        data.whitelist.remove(channel)
        await data.save()

async def get_ban_config(chat_id: int) -> dict:
    """Retrieve ban configuration for a specific chat_id."""
    config = await ChannelWhiteList.get_or_none(chat_id=chat_id).values()
    return config[0]['also_ban'] if config else False

async def set_ban_config(chat_id: int, also_ban: bool) -> None:
    """Set ban configuration for a specific chat_id."""
    data, created = await ChannelWhiteList.get_or_create(chat_id=chat_id)
    data.also_ban = also_ban
    await data.save()