import re
import time
from datetime import datetime
from typing import Callable, Dict, Any, Awaitable, Optional

from aiogram import BaseMiddleware
from aiogram.types import Message

from adapters.db.no_dup import NoDupRepository
from config import config


class MARSMiddleware(BaseMiddleware):
    """
    检测重复转发消息的中间件

    当同一个消息被多次转发到群组时，提醒用户这条消息已经看过了。
    """

    def __init__(self):
        """初始化中间件"""
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any],
    ) -> Any:
        # 只处理群组消息
        if not isinstance(event, Message) or event.chat.type not in [
            "group",
            "supergroup",
        ]:
            return await handler(event, data)

        if not await config.is_feature_enabled("mars", event.chat.id):
            return await handler(event, data)

        # 检查是否是转发消息
        if not self._should_process_forward(event):
            return await handler(event, data)

        # 处理转发消息
        await self._process_forward(event, data)

        return await handler(event, data)

    def _should_process_forward(self, message: Message) -> bool:
        """
        判断是否应该处理这条消息

        根据设计，应该处理：
        - 消息包含 URL
        - 消息转发自一个公开频道

        不处理：
        - 消息转发自其他群
        - 消息转发自本群
        - 消息转发自私有频道
        """
        # 检查是否包含 URL
        has_url = self._extract_urls(message.text or "") or self._extract_urls(
            message.caption or ""
        )

        # 检查是否是转发消息
        if message.forward_from_chat:
            chat = message.forward_from_chat

            # 排除：转发自其他群、本群
            if chat.type in ["group", "supergroup"]:
                # 检查是否转发自本群
                if message.chat.id == chat.id:
                    return False  # 转发自本群，不处理
                else:
                    return False  # 转发自其他群，不处理

            # 排除：转发自私有频道
            if chat.type == "channel" and not chat.username:
                return False  # 私有频道，不处理

            # 处理：转发自公开频道
            if chat.type == "channel" and chat.username:
                return True

        # 处理：消息包含 URL
        if has_url:
            return True

        return False

    def _extract_urls(self, text: str) -> list[str]:
        """从文本中提取 URL"""
        if not text:
            return []

        url_pattern = r"https?://[^\s]+"
        return re.findall(url_pattern, text)

    async def _is_first_of_media_group(self, message: Message) -> bool:
        """
        判断是否是媒体组的第一条消息

        通过检查是否存在相同 media_group_id 且消息 ID 更小的消息来判断
        """
        if not message.media_group_id:
            return True  # 不是媒体组

        # 使用 Telegram API 的消息 ID 来判断顺序
        # 在同一个媒体组内，较小的 message_id 表示较早的消息
        # 由于我们只能访问当前消息，简单的方案是：
        # - 只在 bot 本地缓存中检查
        # - 或者使用一个临时的内存存储来跟踪媒体组

        # 实现方案：使用一个类级别的缓存来存储最近看到的媒体组ID
        if not hasattr(self, "_media_group_cache"):
            self._media_group_cache = {}

        media_group_key = f"{message.chat.id}:{message.media_group_id}"

        if media_group_key in self._media_group_cache:
            # 媒体组已见过，这不是第一条
            return False

        # 记录这个媒体组
        self._media_group_cache[media_group_key] = {
            "message_id": message.message_id,
            "timestamp": datetime.now(),
        }

        # 清理过期的媒体组缓存（超过5分钟的）
        current_time = time.time()
        expired_keys = [
            key
            for key, value in self._media_group_cache.items()
            if (current_time - value["timestamp"].timestamp()) > 300  # 5分钟
        ]
        for key in expired_keys:
            del self._media_group_cache[key]

        return True  # 这是第一条

    async def _process_forward(self, message: Message, data: Dict[str, Any]):
        """
        处理转发消息

        1. 获取原频道消息链接和内容中的 URL
        2. 检查是否是媒体组（只在第一条消息时处理）
        3. 检查数据库
        4. 如果已见过，增加计数并回复提醒
        """
        # 0. 检查媒体组
        # 如果是媒体组的后续消息（不是第一条），跳过处理
        if message.media_group_id:
            # 检查这是否是媒体组的第一条消息
            is_first_of_group = await self._is_first_of_media_group(message)
            if not is_first_of_group:
                # 不是第一条，跳过处理（避免重复计数）
                return

        # 获取所有需要跟踪的链接
        links_to_track = []

        # 1. 获取原频道消息链接
        if message.forward_from_chat and message.forward_from_chat.type == "channel":
            chat = message.forward_from_chat
            channel_name = chat.username or chat.title
            channel_message_id = message.forward_from_message_id

            if channel_name and channel_message_id:
                original_message_link = (
                    f"https://t.me/{channel_name}/{channel_message_id}"
                )
                links_to_track.append(original_message_link)

        # 2. 获取消息中包含的 URL
        text = message.text or ""
        caption = message.caption or ""
        urls = self._extract_urls(text + "\n" + caption)
        links_to_track.extend(urls)

        # 3. 构建当前群内消息的链接
        # 格式：https://t.me/c/{channel_id}/{message_id}
        # 对于私有群：chat_id 格式为 -1001234567890，需要转换为 1234567890
        if message.chat.username:
            current_message_link = (
                f"https://t.me/{message.chat.username}/{message.message_id}"
            )
        else:
            # 私有群，chat_id 为负数，需要转换
            # Telegram Bot API: chat_id = -100XXXXXXXXXX
            # Telegram 链接: https://t.me/c/XXXXXXXXXX/message_id
            channel_id = abs(message.chat.id) - 1000000000000
            current_message_link = f"https://t.me/c/{channel_id}/{message.message_id}"

        # 4. 检查数据库并更新
        previous_message_links = []

        for link in links_to_track:
            record = await NoDupRepository.increment_count(
                message.chat.id,
                link,
                {
                    "message_id": message.message_id,
                    "link": current_message_link,
                    "timestamp": datetime.now().isoformat(),
                    "media_group_id": message.media_group_id,  # 记录媒体组ID
                },
            )

            # 如果计数大于 1，说明见过这条消息
            if record.count > 1:
                previous_message_links = record.forwarded_messages[:-1]

        # 5. 如果看过这条消息，发送提醒
        if previous_message_links:
            await self._send_mars_reminder(message, previous_message_links)

    async def _send_mars_reminder(self, message: Message, previous_messages: list):
        """
        发送"火星了"的提醒

        Args:
            message: 当前转发的消息
            previous_messages: 之前转发过的群内消息列表
        """
        if not message.bot or not message.chat or not message.from_user:
            return

        # 构建提醒消息
        reminder_text = f"你火星了！\n\n"
        reminder_text += "相关的消息之前在群里转发过：\n"

        for msg_info in previous_messages[:3]:  # 最多显示 3 个之前的链接
            link = msg_info.get("link", "")
            reminder_text += f"• {link}\n"

        if len(previous_messages) > 3:
            reminder_text += f"• ... 以及其他 {len(previous_messages) - 3} 条"

        try:
            await message.reply(reminder_text, parse_mode="HTML")
        except Exception as e:
            # 如果回复失败（比如权限不足），记录日志但不中断
            print(f"Failed to send MARS reminder: {e}")

    async def clear_old_records(self, days: int = 30) -> int:
        """清除超过指定天数的旧记录"""
        return await NoDupRepository.clear_old_records(days)
