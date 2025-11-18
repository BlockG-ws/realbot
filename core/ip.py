import logging

import aiohttp


from aiogram.types import Message
from aiogram.utils.formatting import ExpandableBlockQuote, Text, TextLink, Italic


async def handle_ip_command(message: Message):
    """处理 /ip 命令，查询 IP 地址信息"""
    args = message.text.split(' ')
    if len(args) < 2:
        await message.reply("用法： /ip IP地址")
        return
    ip_address = args[1]
    ip_regex = ('^(?:(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9]).){3}(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?['
                '0-9])$|^((?:[0-9A-Fa-f]{1,4}(?::[0-9A-Fa-f]{1,4}){7})|(?:(?![A-Fa-f0-9]*::)(?:[0-9A-Fa-f]{1,'
                '4}(?::[0-9A-Fa-f]{1,4}){0,6})?::(?:[0-9A-Fa-f]{1,4}(?::[0-9A-Fa-f]{1,4}){0,6})?)|(?:[0-9A-Fa-f]{1,'
                '4}(?::[0-9A-Fa-f]{1,4}){0,4}:(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])(?:.(?:25[0-5]|2[0-4]['
                '0-9]|1[0-9]{2}|[1-9]?[0-9])){3}))$')
    import re
    if not re.match(ip_regex, ip_address):
        await message.reply("无效的 IP 地址格式，请提供有效的 IPv4 或 IPv6 地址")
        return
    await message.bot.send_chat_action(message.chat.id, 'typing')
    info = await generate_msg(await get_info(ip_address))
    if not info:
        await message.reply(f"未能查询到该 IP 地址的信息。但你可以尝试访问以下网站进行查询：\n {TextLink('HTML.ZONE',url=f'https://html.zone/ip/query/?ip={ip_address}').as_html()}\n {TextLink('iplark',url=f'https://iplark.com/{ip_address}').as_html()}",disable_web_page_preview=True)
        return
    await message.reply(f'{Text(ExpandableBlockQuote(info)).as_html()}\n你也可以尝试访问以下网站进行查询：\n {TextLink('HTML.ZONE',url=f'https://html.zone/ip/query/?ip={ip_address}').as_html()}\n {TextLink('iplark',url=f'https://iplark.com/{ip_address}').as_html()}\n\n{Italic('以上数据来源于第三方，数据的真实性 bot 不做保证。').as_html()}',disable_web_page_preview=True)

async def generate_msg(data: dict) -> str:
    """根据查询到的 IP 信息生成回复消息"""
    lines = []
    if not data:
        return ""
    for key, value in data.items():
        lines.append(f"来自 {key} 的数据：")
        if not value:
            lines.append("  未能获取到信息。\n")
            continue
        if isinstance(value, dict):
            for ik, iv in value.items():
                lines.append(f"  {ik}: {iv}")
        else:
            lines.append(f"  {value}")
        lines.append("")  # 添加空行分隔不同数据源
    return "\n".join(lines)

async def get_info(ip_address: str) -> dict:
    """查询 IP 地址信息的主函数，同时尝试多个数据源"""
    data_sources = [ipinfo, ipsb_info, meituan_ipinfo, bilibili_ipinfo]
    import asyncio
    tasks = [source(ip_address) for source in data_sources]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    merged: dict = {}
    for idx, res in enumerate(results):
        if isinstance(res, Exception):
            logging.warning(f"查询 IP 地址信息时，数据源 {data_sources[idx].__name__} 出现错误: {res}")
            continue
        merged[data_sources[idx].__name__] = res
    return merged if merged else {}


async def ipinfo(ip_address: str) -> dict:
    """从 ipinfo.io 查询 IP 地址信息的辅助函数"""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://ipinfo.io/{ip_address}/json") as resp:
            if resp.status != 200:
                return {}
            data = await resp.json()
            data.pop("readme", None)  # 移除无用的 readme 字段
            return dict(sorted(data.items()))

async def ipsb_info(ip_address: str) -> dict:
    """从 ip.sb 查询 IP 地址信息的辅助函数"""
    from datetime import datetime
    import pytz
    tz = pytz.timezone('Asia/Shanghai')
    ts = int(datetime.now(tz).timestamp())
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.ip.sb/geoip/{ip_address}?_t={ts}") as resp:
            if resp.status != 200:
                return {}
            data = await resp.json()
            return dict(sorted(data.items()))

async def meituan_ipinfo(ip_address: str) -> dict:
    """从美团查询 IP 地址信息的辅助函数"""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://apimobile.meituan.com/locate/v2/ip/loc?rgeo=true&ip={ip_address}") as resp:
            if resp.status != 200:
                return {}
            data = await resp.text()
            import json
            data = json.loads(data)
            data_as_dict = data.get("data", {})
            rgeo = data_as_dict.get('rgeo',{})
            if rgeo:
                if isinstance(rgeo, dict):
                    merged = ''
                    rgeo.pop('adcode', None)  # 移除邮政编码字段
                    for subk, subv in rgeo.items():
                        merged += f"{subv}"
                    data_as_dict['rgeo'] = merged
            return dict(sorted(data_as_dict.items()))

async def bilibili_ipinfo(ip_address: str) -> dict:
    """从哔哩哔哩查询 IP 地址信息的辅助函数"""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.live.bilibili.com/ip_service/v1/ip_service/get_ip_addr?ip={ip_address}",headers={'user-agent':'curl/8.0.0'}) as resp:
            # 不知为何必须改 user-agent 才能返回数据
            if resp.status != 200:
                return {}
            data = await resp.json()
            data_field = data.get("data", {})
            if isinstance(data_field, dict):
                def _is_empty(v):
                    if v is None:
                        return True
                    if isinstance(v, str) and not v.strip():
                        return True
                    if isinstance(v, (list, tuple, dict)) and len(v) == 0:
                        return True
                    return False
                return {k: v for k, v in data_field.items() if not _is_empty(v)}
            return dict(sorted(data.items()))