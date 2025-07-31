from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable
import json

class MessageStatsMiddleware(BaseMiddleware):
    def __init__(self, stats_file: str = 'message_stats.json'):
        self.stats_file = stats_file
        self.stats = self.load_stats()

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # 只统计群组消息
        if event.chat.type in ['group', 'supergroup']:
            chat_id = str(event.chat.id)
            user_id = str(event.from_user.id if event.from_user else 0)

            # 初始化统计数据
            if chat_id not in self.stats:
                self.stats[chat_id] = {
                    'total_messages': 0,
                    'users': {},
                    'chat_title': event.chat.title
                }

            if user_id not in self.stats[chat_id]['users']:
                name = 'Unknown'
                if event.sender_chat:
                    if event.sender_chat.type in ['group','supergroup']:
                        # 如果是频道/群组匿名管理员消息，使用频道名称
                        name = f"{event.sender_chat.title} [admin]"
                    # 如果是频道/群组匿名管理员消息，使用频道名称
                    name = f"{event.sender_chat.title} [channel]"
                elif event.from_user:
                    name = event.from_user.full_name
                self.stats[chat_id]['users'][user_id] = {
                    'message_count': 0,
                    'xm_count': 0,
                    'wocai_count': 0,
                    'username': event.from_user.username if event.from_user else 'Unknown',
                    'name': name
                }

            # 更新统计
            self.stats[chat_id]['total_messages'] += 1
            self.stats[chat_id]['users'][user_id]['message_count'] += 1
            # 羡慕、我菜统计
            if event.text and any(keyword in event.text.lower() for keyword in ['xm','xmsl','羡慕','羡慕死了']):
                if not self.stats[chat_id]['users'][user_id]['xm_count']:
                    self.stats[chat_id]['users'][user_id]['xm_count'] = 0
                self.stats[chat_id]['users'][user_id]['xm_count'] += 1
            if event.sticker and event.sticker.file_unique_id in ['AQADhhcAAs1rgFVy']:
                if not self.stats[chat_id]['users'][user_id]['xm_count']:
                    self.stats[chat_id]['users'][user_id]['xm_count'] = 0
                self.stats[chat_id]['users'][user_id]['xm_count'] += 1

            if event.text and '我菜' in event.text:
                if not self.stats[chat_id]['users'][user_id]['wocai_count']:
                    self.stats[chat_id]['users'][user_id]['xm_count'] = 0
                self.stats[chat_id]['users'][user_id]['wocai_count'] += 1
            if event.sticker and event.sticker.file_unique_id in ['AQAD6AUAAgGeUVZy']:
                if not self.stats[chat_id]['users'][user_id]['wocai_count']:
                    self.stats[chat_id]['users'][user_id]['wocai_count'] = 0
                self.stats[chat_id]['users'][user_id]['wocai_count'] += 1
            # 保存统计数据
            self.save_stats()

        return await handler(event, data)

    def load_stats(self) -> dict:
        try:
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_stats(self):
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)