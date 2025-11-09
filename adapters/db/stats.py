import asyncio
import json

from tortoise import Tortoise
from tortoise.expressions import F

from adapters.db.models import Stats

async def get_group_stats(chat_id: int) -> dict[str, dict]:
    """Retrieve statistics for a specific group chat by chat_id."""
    stats = await Stats.get(chat_id=chat_id).values()
    return stats

async def get_24h_message_stats(chat_id: int) -> dict:
    """Retrieve 24-hour message statistics for a specific group chat."""
    stats = await Stats.get(chat_id=chat_id)
    return stats.messages_24h or {}

async def get_user_stats(chat_id: int, user_id: int) -> dict:
    """Retrieve statistics for a specific user in a group chat."""
    stats = await Stats.get(chat_id=chat_id)
    users_data = stats.users
    if users_data and str(user_id) in users_data:
        return users_data[str(user_id)]
    return {}

async def update_group_stats(chat_id: int, user_id: int) -> None:
    """Update statistics for a specific group chat."""
    from datetime import datetime
    stats = await Stats.get(chat_id=chat_id)
    # JSON 只能使用字符串作为键，所以将 user_id 转换为字符串
    uid = str(user_id)
    stats.total_messages = (stats.total_messages or 0) + 1
    messages_24h = stats.messages_24h or {"messages": [], "message_count": 0, "active_users": {}}
    messages_24h["message_count"] = messages_24h["message_count"] + 1
    messages_24h["active_users"][uid] = messages_24h["active_users"].get(uid, 0) + 1
    messages_24h["messages"].append({"user_id": user_id, "timestamp": datetime.now().isoformat()})
    stats.messages_24h = messages_24h
    await stats.save()

async def update_24h_message(chat_id: int, data: dict) -> None:
    """Update the 24-hour message count for a specific group chat."""
    stats = await Stats.get(chat_id=chat_id)
    stats.messages_24h = data
    await stats.save()

async def update_user_stats(chat_id: int, user_id: int, username: str, name: str,attr: None | str) -> None:
    """Update statistics for a specific user in a group chat."""
    stats = await Stats.get(chat_id=chat_id)
    users_data = stats.users or {}
    uid = str(user_id)
    user_data = users_data.get(uid, {})
    if not attr:
        user_data["username"] = username
        user_data["name"] = name
        user_data["message_count"] = user_data.get("message_count", 0) + 1
    elif attr in ("xm_count","wocai_count"):
        user_data[attr] = user_data.get(attr, 0) + 1
    users_data[uid] = user_data
    stats.users = users_data
    await stats.save()