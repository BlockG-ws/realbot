import logging
import time
from collections import deque, defaultdict
from dataclasses import dataclass

from aiogram import BaseMiddleware, Router
from aiogram.types import Message
from typing import Dict, Callable, Awaitable, Any

router = Router()

# 根据某只狐狐自己发的计算公式试图重构了这部分
# 这个代码的目的是计算用户的欠打度，因为他的公式是用 AI 生成的，所以我也用 AI 生成了这个代码
# AI 太好用了你们知道吗.jpg
# 然后限于条件（比如我没有模型可以拿来分类）对公式进行了一部分精简，比如去除了发情度和理性度的计算，加大了对于别人 /打 的惩罚力度
@dataclass
class UserMetrics:
    """用户指标数据类"""
    cai_count: int = 0  # 卖菜度发言数
    xm_count: int = 0   # 羡慕度发言数
    nsfw_count: int = 0 # NSFW度发言数
    antisocial_count: int = 0 # 反社会度发言数
    total_count: int = 0 # 总发言数
    neutral_count: int = 0 # 中性发言数（用于水群频率）


class RikkiMiddleware(BaseMiddleware):
    def __init__(self, target_user_id: str = "5545347637"):
        # 存储每个用户的触发几率，初始值在40-50%之间
        self.user_probabilities: Dict[str, float] = {}
        # 触发关键词
        self.xm_keywords = ["啃", "羡慕", "xm", "xmsl", "羡慕死了", "我菜"]
        self.cai_keywords = ["菜", "菜了", "菜死了", "我菜", "废物"]
        self.nsfw_keywords = ["kig", "电你", "被电", "⚡", "tk", "打", "🌿我"]

        self.target_user_id = target_user_id

        # 权重配置
        self.weights = {
            'w_v': 20,  # 卖菜度权重
            'w_m': 15,  # 羡慕度权重
            'w_n': 30,  # NSFW度权重
            'w_a': 30,  # 反社会度权重
            'lambda': 1,  # 水群缓冲系数
        }

        # 放大系数
        self.amplifiers = {
            'alpha_v': 2.5,  # 卖菜度放大系数
            'beta_m': 2.0,  # 羡慕度放大系数
            'gamma_n': 5.0,  # NSFW度放大系数
            'alpha_a': 5.0,  # 反社会度放大系数
        }

        # 用户数据存储
        self.user_metrics: Dict[str, UserMetrics] = defaultdict(UserMetrics)
        self.user_message_times: Dict[str, deque] = defaultdict(lambda: deque())
        self.has_sent_warning: Dict[str, bool] = defaultdict(bool)


    def record_message(self, user_id: str) -> None:
        """记录用户发送消息的时间"""
        current_time = time.time()
        user_messages = self.user_message_times[user_id]

        # 添加当前时间戳
        user_messages.append(current_time)

        # 清理24小时前的记录
        cutoff_time = current_time - 24 * 60 * 60  # 24小时前
        while user_messages and user_messages[0] < cutoff_time:
            user_messages.popleft()

    def get_24h_message_count(self, user_id: str) -> int:
        """获取用户24小时内的发言次数"""
        current_time = time.time()
        cutoff_time = current_time - 24 * 60 * 60

        # 清理过期记录
        user_messages = self.user_message_times[user_id]
        while user_messages and user_messages[0] < cutoff_time:
            user_messages.popleft()

        return len(user_messages)

    def classify_message(self, message: str, user_id: str) -> None:
        """分析消息内容并更新用户指标"""
        metrics = self.user_metrics[user_id]
        metrics.total_count += 1

        message_lower = message.lower()
        classified = False

        # 检查各类关键词
        for keyword in self.cai_keywords:
            if keyword in message_lower:
                metrics.cai_count += 1
                classified = True
                break

        for keyword in self.xm_keywords:
            if keyword in message_lower:
                metrics.xm_count += 1
                classified = True
                break

        for keyword in self.nsfw_keywords:
            if keyword in message_lower:
                metrics.nsfw_count += 1
                classified = True
                break

        # 如果没有匹配任何特征关键词，算作中性发言
        if not classified:
            metrics.neutral_count += 1

    def calculate_qianda_score(self, user_id: str) -> float:
        """计算用户欠打度"""
        if user_id != self.target_user_id:
            return 0.0

        metrics = self.user_metrics[user_id]

        if metrics.total_count == 0:
            return 0.0

        # 计算各项指标 [0,1]
        v = min(1, self.amplifiers['alpha_v'] * (metrics.cai_count / metrics.total_count))
        m = min(1, self.amplifiers['beta_m'] * (metrics.xm_count / metrics.total_count))
        n = min(1, self.amplifiers['gamma_n'] * (metrics.nsfw_count / metrics.total_count))
        a = min(1, self.amplifiers['alpha_a'] * (metrics.antisocial_count / metrics.total_count))

        # 计算水群频率缓冲因子 W
        # N 是24小时内中性发言次数，K设为7
        k = 7
        import math
        neutral_24h = min(metrics.neutral_count, self.get_24h_message_count(user_id))
        w = min(max(0, 1 - math.log(neutral_24h + 1) / k), 1)

        # 应用欠打度公式
        base_score = (
                v * self.weights['w_v'] +
                m * self.weights['w_m'] +
                n * self.weights['w_n'] +
                a * self.weights['w_a']
        )

        water_factor = 1 + self.weights['lambda'] * (1 - w)

        final_score = min(100, base_score * water_factor)

        return final_score


    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]) -> Any:
        """
        处理消息的主要方法
        """
        if not event.text:
            return await handler(event, data)

        user_id = str(event.from_user.id)
        if event.chat.type in ['group', 'supergroup'] and user_id == self.target_user_id:
            self.classify_message(event.text, user_id)
            score = self.calculate_qianda_score(user_id)
            logging.debug(f"当前欠打度: {score:.2f}%")

            # 警告阈值：80%
            if score >= 80.0 and not self.has_sent_warning[user_id]:
                self.has_sent_warning[user_id] = True
                await event.reply("泥欠打了")

            # 检查是否触发
            if score >= 100.0:
                # 重置数据
                self.user_metrics[user_id] = UserMetrics()
                self.has_sent_warning[user_id] = False
                await event.reply("/打")

        if event.text and event.text.startswith('/打') and event.reply_to_message and str(
                event.reply_to_message.from_user.id) == self.target_user_id:
            # 增加反社会度作为惩罚
            metrics = self.user_metrics[self.target_user_id]
            metrics.antisocial_count += 2  # 被打时额外增加反社会度
            score = self.calculate_qianda_score(user_id)
            logging.debug("当前欠打的几率是{}".format(score))

        return await handler(event, data)

    def get_user_status(self, user_id: str) -> str:
        """获取用户当前几率状态（用于调试）"""
        score = self.calculate_qianda_score(user_id)
        metrics = self.user_metrics[user_id]

        return (f"欠打度: {score:.2f}%\n"
                f"卖菜: {metrics.cai_count}, 羡慕: {metrics.xm_count}, "
                f"NSFW: {metrics.nsfw_count},"
                f"反社会: {metrics.antisocial_count}, 中性: {metrics.neutral_count}\n"
                f"总发言: {metrics.total_count}")