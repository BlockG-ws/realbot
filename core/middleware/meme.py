import logging
from typing import Callable, Dict, Awaitable, Any
from config import config
from aiogram import BaseMiddleware
from aiogram.types import Message


class ThreeKingdomsMiddleWare(BaseMiddleware):
    def __init__(self) -> None:
        self.counter = 0

    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ) -> Any:
        text = event.text or event.caption
        if 'group' in event.chat.type:
            if "风从虎" in text and "云从龙" in text and not "龙虎英雄傲苍穹" in text:
                await event.reply("龙虎英雄傲苍穹")
            if "吃什么" in text and not "是啊" in text:
                await event.reply("是啊，吃什么")
            if "仁之剑" in text:
                if not "义之剑" in text:
                    await event.reply("一把叫义之剑")
                else:
                    await event.reply("可别逼我使出无情剑来")
            if "酸" in text and not "不怕" in text and not "眼都酸了" in text:
                await event.reply("可咱家说了咱家不怕酸，不怕！")
            if "眼都酸了" in text and not "膀子" in text and not "不酸" in text:
                await event.reply("他们的膀子竟然不酸")
            if "我打了一辈子仗" in text and not "享受" in text:
                await event.reply("就不能享受享受吗！")
            if "我上表" in text and "让" in text and "已经回消息了" in text and not "竟然不许" in text:
                await event.reply("竟！然！不！许！")
            if "那好啊" in text and not "过江" in text:
                await event.reply("他过江我也过江！")
            if "再让我听到" in text and "扎聋我自己的耳朵" in text:
                await event.reply("聋，可是帝王之征啊")
            if "说两句" in text and ("得了" in text or "行了" in text):
                await event.reply("谁知道先帝爷听得见听不见")
            if "三军听令" in text and not "自刎归天" in text:
                await event.reply("自刎归天")
            if "笑面虎" in text and not "乌角鲨" in text:
                await event.reply("两头乌角鲨")
            if "死不可怕" in text and not "凉爽的夏夜" in text:
                await event.reply("死亡是凉爽的夏夜，可供人无忧地安眠")
            if "跳跳虎" in text and not "脆脆鲨" in text:
                await event.reply("两头脆脆鲨")
            import random
            if random.randint(1,1000) == 1:
                await event.reply("此话说的痛切，当浮一大白")
        return await handler(event, data)