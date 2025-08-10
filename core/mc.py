import logging

from aiogram.enums import ParseMode
from aiogram.types import Message


async def handle_mc_status_command(message: Message):
    """Handle the /mc command to check Minecraft server status."""
    args = message.text.replace('/mc', '').strip().split(' ')
    server_type = args[0] if args else 'java'
    server_address = args[1] if len(args) >= 2 else None
    query_enabled = True if len(args) >= 3 and args[2] == 'query' else False
    if not args:
        await message.reply("Usage: /mc <java/bedrock> <server_address>\n"
                            "Example: /mc java play.example.com")
        return
    if not server_address:
        await message.reply("你没有提供服务器地址")
        return
    import re
    local_ip_regex = r'^(?:(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:(?:1[6-9])|(?:2[0-9])|(?:3[0-1]))\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|127\.\d{1,3}\.\d{1,3}\.\d{1,3})(?::\d{1,5})?)$'
    if re.match(local_ip_regex, server_address) or server_address == 'localhost' or any(server_address == address for address in ['::1', 'fe80::', '.lan']):
        await message.reply("正在与本地服务器断开连接")
        return
    if server_address == 'dinnerbone.com':
        await message.reply("ɯoɔ˙ǝuoqɹǝuuᴉp/ǝlᴉɟoɹd/ddɐ˙ʎʞsq//:sdʇʇɥ")
        # https://bsky.app/profile/dinnerbone.com , but typical dinnerbone style
        return
    status_message = await message.reply('正在查询服务器状态...')
    if server_type == 'java':
        try:
            from mcstatus import JavaServer
            server = await JavaServer.async_lookup(server_address)
            status = await server.async_status()
            query = None
            s_message = f"这个 Java 服务器"
            # 尝试查询服务器信息
            if query_enabled:
                try:
                    query = await server.async_query()
                except Exception as e:
                    s_message = f"_我未能成功发送 query 请求，可能是因为服务器未开放对应端口。_\n这个 Java 服务器"
                    logging.warning('查询 Minecraft 服务器遇到了错误',e)
            if query:
                s_message = f"这个 Java 服务器使用了 {query.software.brand}({query.software.version})，"
            s_message += f"有{status.players.online}(/{status.players.max}) 人在线\n"
            s_message += "延迟大约有 {:.2f} ms\n".format(status.latency)
            s_message += f"服务器的 MOTD 是: ```\n{status.motd.to_minecraft()}\n```"
            s_message += f"版本信息: {status.version.name} ({status.version.protocol})\n"
            s_message += f"你应该使用和上面的版本相同的 Minecraft 客户端连接这个服务器。\n"
            if (not query) and status.players.sample:
                s_message += f"在线玩家列表: \n{', '.join(player.name for player in status.players.sample)}\n"
            if query and query.software.plugins:
                s_message += f"服务器插件: {', '.join(query.software.plugins)}\n"
            if query and query.players.names:
                s_message += f"查询到的玩家: {', '.join(query.players.names)}\n"
            if status.forge_data:
                s_message += f"看起来这是一个有 mod 的服务器。\n"
            if status.enforces_secure_chat:
                s_message += "服务器启用了消息签名，这意味着你需要调整 No Chat Reports 等类似 mod 的设置。\n\n"
            s_message += "声明：这些结果均为服务器所公开的信息。查询结果仅代表bot所在的服务器对该服务器的查询结果，可能与实际情况有出入。"
            await status_message.edit_text(s_message, parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await status_message.edit_text(f"悲报\n服务器连接失败\n{str(e)}")
    elif server_type == 'bedrock':
        try:
            from mcstatus import BedrockServer
            server = BedrockServer.lookup(server_address)

            status = await server.async_status()

            # 稍微汉化一下这个状态信息
            if status.gamemode == 'Survival':
                game_mode = '生存'
            elif status.gamemode == 'Creative':
                game_mode = '创造'
            else:
                game_mode = status.gamemode or '未知模式'

            s_message = f"这个基岩版{game_mode}服务器有 {status.players.online}(/{status.players.max})人在线游玩{status.map_name or '一张地图'}，\n"
            if status.version.brand == 'MCEE':
                s_message += "这个服务器是 Minecraft 教育版服务器。\n"
            s_message += "延迟大约有 {:.2f} ms\n".format(status.latency)
            s_message += f"服务器的 MOTD 是: ```\n{status.motd.to_minecraft()}\n```"
            s_message += f"版本信息: {status.version.name or status.version.version} ({status.version.protocol})\n"
            s_message += f"你应该使用和上面的版本相同的 Minecraft 客户端连接这个服务器。\n\n"
            s_message += "声明：这些结果均为服务器所公开的信息。这个查询结果仅代表bot所在的服务器对该服务器的查询结果，可能与实际情况有出入。"
            await status_message.edit_text(s_message, parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await status_message.edit_text(f"悲报\n服务器连接失败\n {str(e)}")
    else:
        await status_message.edit_text("未知的服务器类型，请使用 'java' 或 'bedrock'")
