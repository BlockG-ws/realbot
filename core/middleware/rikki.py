import random
from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Dict, Optional, Callable, Awaitable, Any


class RikkiMiddleware(BaseMiddleware):
    def __init__(self, target_user_id: str = "5545347637"):
        # 存储每个用户的触发几率，初始值在40-50%之间
        self.user_probabilities: Dict[str, float] = {}
        # 触发关键词
        self.trigger_plus_keywords = ["啃","羡慕", "xm", "xmsl", "羡慕死了", "我菜"]
        self.trigger_plusplus_keywords = ["kig","电你","被电","⚡","tk","打"]
        self.target_user_id = target_user_id

    def get_user_probability(self, user_id: str) -> float:
        """获取用户当前触发几率，如果不存在则初始化"""
        if user_id != self.target_user_id:
            return 0.0 # 非目标用户返回默认值
        if user_id not in self.user_probabilities:
            self.user_probabilities[user_id] = random.uniform(10.0, 40.0)
        return self.user_probabilities[user_id]

    def update_probability(self, user_id: str, message: str, hit_by_others = False) -> float:
        """更新用户触发几率"""
        if user_id != self.target_user_id:
            return 0.0 # 非目标用户不更新
        current_prob = self.get_user_probability(user_id)

        # 基础减少0.1%
        current_prob -= 0.1

        # 检查是否包含触发关键词
        for keyword in self.trigger_plus_keywords:
            if keyword in message:
                current_prob *= 1.14
                break
        for keyword in self.trigger_plusplus_keywords:
            if keyword in message:
                current_prob *= 1.91
                break
        if hit_by_others:
            # 如果被其他人触发，增加额外几率
            current_prob += 20.0
        self.user_probabilities[user_id] = current_prob
        return current_prob

    def should_trigger(self, user_id: str) -> bool:
        """检查是否应该触发回复"""
        if user_id != self.target_user_id:
            return False  # 非目标用户不触发
        probability = self.get_user_probability(user_id)
        return probability >= 100.0

    def reset_probability(self, user_id: str):
        """重置用户触发几率到初始随机值"""
        self.user_probabilities[user_id] = random.uniform(40.0, 50.0)

    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ) -> Any:
        """
        处理消息的主要方法
        """
        if not event.text:
            return await handler(event, data)
        user_id = str(event.from_user.id)
        if event.chat.type in ['group', 'supergroup'] and user_id == self.target_user_id:
            # 更新几率
            self.update_probability(user_id, event.text)

        if event.text and event.text.startswith('/打') and event.reply_to_message and str(event.reply_to_message.from_user.id) == self.target_user_id:
            self.update_probability(user_id, event.text, hit_by_others=True)

        if self.get_user_probability(user_id) >= 80.0:
            await event.reply("泥欠打了")

        # 检查是否触发
        if self.should_trigger(user_id):
            # 重置几率
            self.reset_probability(user_id)
            await event.reply("/打")
        return await handler(event, data)

    def get_probability_status(self, user_id: str) -> str:
        """获取用户当前几率状态（用于调试）"""
        prob = self.get_user_probability(user_id)
        return f"当前触发几率: {prob:.2f}%"