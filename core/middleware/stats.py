from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable

from datetime import datetime, timedelta
from adapters.db.stats import update_group_stats, update_user_stats, get_24h_message_stats, update_24h_message
from config import config


async def cleanup_old_messages(chat_id: int):
    """清理超过24小时的消息记录"""
    messages_24h = await get_24h_message_stats(chat_id)
    if not messages_24h:
        return

    messages = messages_24h.get('messages')
    if not messages:
        # ensure structure exists for downstream code
        messages_24h.setdefault('messages', [])
        messages_24h.setdefault('messages_24h', {})
        messages_24h.setdefault('active_users', {})
        return

    cutoff_time = datetime.now() - timedelta(hours=24)
    cleaned_messages = []
    for msg in messages:
        ts = msg.get('timestamp')
        if ts is None:
            continue
        try:
            msg_time = datetime.fromisoformat(ts) if isinstance(ts, str) else datetime.fromtimestamp(float(ts))
        except Exception:
            # Skip messages with invalid timestamp formats
            continue
        if msg_time > cutoff_time:
            cleaned_messages.append(msg)

    messages_24h['messages'] = cleaned_messages

    # Update message count safely
    messages_24h.setdefault('messages_24h', {})
    messages_24h['messages_24h']['message_count'] = len(cleaned_messages)

    # Recompute active users (count messages per user), skip entries without user_id
    active_users_dict = {}
    for msg in cleaned_messages:
        user_id = msg.get('user_id')
        if user_id is None:
            continue
        active_users_dict[user_id] = active_users_dict.get(user_id, 0) + 1
    messages_24h['active_users'] = active_users_dict
    # 保存更新后的24小时消息统计到数据库
    await update_24h_message(chat_id, messages_24h)


class MessageStatsMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # 只统计群组消息
        if not await config.is_feature_enabled('stats', event.chat.id):
            return await handler(event, data)
        if event.chat.type in ['group', 'supergroup']:
            chat_id = event.chat.id
            user_id = event.from_user.id if event.from_user else 0

            username = event.from_user.username if event.from_user else None
            name = 'Unknown'
            if event.sender_chat:
                if event.sender_chat.type in ['group','supergroup']:
                    # 如果是频道/群组匿名管理员消息，使用频道名称
                    name = f"{event.sender_chat.title} [admin]"
                # 如果是频道/群组匿名管理员消息，使用频道名称
                name = f"{event.sender_chat.title} [channel]"
            elif event.from_user:
                name = event.from_user.full_name

            # 更新统计
            await update_group_stats(chat_id, user_id)
            # 更新活跃用户统计
            await update_user_stats(chat_id, user_id, username, name, attr=None)

            # 羡慕、我菜统计
            if event.text and any(keyword in event.text for keyword in ['xm','xmsl','羡慕','羡慕死了']):
                await update_user_stats(chat_id, user_id, username, name, attr='xm_count')

            if event.sticker and event.sticker.file_unique_id in ['AQADhhcAAs1rgFVy']:
                await update_user_stats(chat_id, user_id, username, name, attr='xm_count')

            if event.text and '我菜' in event.text:
                await update_user_stats(chat_id, user_id, username, name, attr='wocai_count')
            if event.sticker and event.sticker.file_unique_id in ['AQAD6AUAAgGeUVZy']:
                await update_user_stats(chat_id, user_id, username, name, attr='wocai_count')

            # 清理超过24小时的记录
            await cleanup_old_messages(chat_id)

        return await handler(event, data)

