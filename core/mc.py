import logging
import json
import os

from aiogram.enums import ParseMode
from aiogram.types import Message

async def lookup_java_server(query_enabled,server_address):
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
                    logging.warning('查询 Minecraft 服务器遇到了错误', e)
            if query:
                s_message = f"这个 Java 服务器使用了 {query.software.brand}({query.software.version})，"
            s_message += f"有{status.players.online}(/{status.players.max}) 人在线\n"
            s_message += "延迟大约有 {:.2f} ms\n".format(status.latency)
            s_message += f"服务器的 MOTD 是: ```\n{status.motd.to_minecraft()}\n```"
            s_message += f"版本信息: {status.version.name} ({status.version.protocol})\n"
            s_message += f"你应该使用和上面的版本相同的 Minecraft 客户端连接这个服务器。\n"
            if (not query) and status.players.sample:
                s_message += f"在线玩家列表: \n{', '.join(player.name.replace('_',r'\_') for player in status.players.sample)}\n"
            if query and query.software.plugins:
                s_message += f"服务器插件: {', '.join(query.software.plugins)}\n"
            if query and query.players.names:
                s_message += f"查询到的玩家: {', '.join(query.players.names).replace('_',r'_')}\n"
            if status.forge_data:
                s_message += f"看起来这是一个有 mod 的服务器。\n"
            if status.enforces_secure_chat:
                s_message += "服务器启用了消息签名，这意味着你需要调整 No Chat Reports 等类似 mod 的设置。\n\n"
            s_message += "声明：这些结果均为服务器所公开的信息。查询结果仅代表bot所在的服务器对该服务器的查询结果，可能与实际情况有出入。"
        except Exception as e:
            s_message = f"悲报\n服务器连接失败\n{str(e)}"
        return s_message

async def lookup_bedrock_server(server_address):
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
    except Exception as e:
        s_message = f"悲报\n服务器连接失败\n {str(e)}"
    return s_message


async def handle_mc_status_command(message: Message):
    """Handle the /mc command to check Minecraft server status."""
    args = message.text.replace('/mc', '').strip().split(' ')
    bind_file = 'mc_bindings.json'
    if args == ['']:
        # Load existing bindings
        if os.path.exists(bind_file):
            with open(bind_file, 'r', encoding='utf-8') as f:
                bindings = json.load(f)
        else:
            bindings = {}
        chat_bindings = bindings.get(str(message.chat.id), {})
        available_types = [t for t, addr in chat_bindings.items() if addr is not None]
        if message.chat.type in ['group', 'supergroup'] and chat_bindings and available_types:
            server_address = chat_bindings.get(available_types[0], None)
            status_message = await message.reply('正在查询服务器状态...')
            if available_types[0] == 'java':
                s_message = await lookup_java_server(False, server_address)
                await status_message.edit_text(s_message, parse_mode=ParseMode.MARKDOWN)
            elif available_types[0] == 'bedrock':
                s_message = await lookup_bedrock_server(server_address)
                await status_message.edit_text(s_message, parse_mode=ParseMode.MARKDOWN)
            else:
                await status_message.edit_text("未知的服务器类型，请使用 'java' 或 'bedrock'")
            return
        else:
            await message.reply("Usage: /mc <bind/server> <java/bedrock> <server_address>\n"
                                "Example: /mc server java play.example.com")
        return

    option = args[0] if args else None
    server_type = args[1] if args else 'java'
    server_address = args[2] if len(args) >= 3 else None
    query_enabled = True if len(args) >= 4 and args[3] == 'query' else False
    if option not in ['bind', 'server']:
        await message.reply("Invalid option. Use 'bind' or 'server'.")
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
    if option == 'bind':
        if not message.chat.type in ['group', 'supergroup']:
            await message.reply("这个命令只能在群组中使用")
            return
        bind_file = 'mc_bindings.json'

        # Load existing bindings
        if os.path.exists(bind_file):
            with open(bind_file, 'r', encoding='utf-8') as f:
                bindings = json.load(f)
        else:
            bindings = {}

        # Get chat ID
        chat_id = str(message.chat.id)

        # Initialize chat binding if not exists
        if chat_id not in bindings:
            bindings[chat_id] = {'java': None, 'bedrock': None}

        # Update the binding for the specified server type
        bindings[chat_id][server_type] = server_address

        # Save bindings back to file
        with open(bind_file, 'w', encoding='utf-8') as f:
            json.dump(bindings, f, ensure_ascii=False, indent=2)

        await message.reply(f"已成功绑定 {server_type} 服务器: {server_address}")
        return
    if option == 'server':
        status_message = await message.reply('正在查询服务器状态...')
        if server_type.lower() == 'java':
            s_message = await lookup_java_server(query_enabled, server_address)
            await status_message.edit_text(s_message, parse_mode=ParseMode.MARKDOWN)
        elif option == 'server' and server_type.lower() == 'bedrock':
            s_message = await lookup_bedrock_server(server_address)
            await status_message.edit_text(s_message, parse_mode=ParseMode.MARKDOWN)
        else:
            await status_message.edit_text("未知的服务器类型，请使用 'java' 或 'bedrock'")

