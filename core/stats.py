from aiogram.types import Message
import json

from config import config


async def handle_stats_command(message: Message):
    """处理统计命令"""
    if not config.is_feature_enabled('stats', message.chat.id):
        return
    if message.chat.type not in ['group', 'supergroup']:
        await message.reply("此命令仅在群组中可用")
        return
    chat_id = str(message.chat.id)
    try:
        with open('message_stats.json', 'r', encoding='utf-8') as f:
            stats = json.load(f).get(chat_id)
    except (FileNotFoundError, json.JSONDecodeError):
        stats = {}.get(chat_id)

    if not stats:
        await message.reply("暂无统计数据")
        return

    stats_message = await message.reply("正在生成统计信息...")

    # 按消息数量排序用户
    sorted_users = sorted(
        stats['users'].items(),
        key=lambda x: x[1]['message_count'],
        reverse=True
    )
    sorted_24h_users = sorted(
        [(user_id, stats['users'][user_id]) for user_id in stats.get('messages_24h', {}).get('active_users', [])],
        key=lambda x: x[1]['message_count'],
        reverse=True
    )
    sorted_most_xm_users = sorted(
        stats['users'].items(),
        key=lambda x: x[1].get('xm_count',0),
        reverse=True
    )
    sorted_most_wocai_users = sorted(
        stats['users'].items(),
        key=lambda x: x[1].get('wocai_count',0),
        reverse=True
    )


    # 构建统计消息
    text = f"📊 群组统计\n\n"
    text += f"总消息数: {stats['total_messages']}\n"
    text += f"24小时内消息数: {stats['messages_24h']['message_count']}\n"
    text += f"活跃用户数: {len(stats['users'])}\n"
    text += f"24小时内活跃用户数:{len(stats['messages_24h']['active_users'])}\n\n"
    text += "🏆 发言排行榜:\n"
    text += "<blockquote expandable>"
    for i, (user_id, user_data) in enumerate(sorted_users[:10], 1):
        name = user_data['name'] or user_data['username'] or str(user_id)
        text += f"{i}. {name}: {user_data['message_count']} 条\n"
    text += "</blockquote>\n"
    text += "📈 24小时内发言排行榜:\n"
    text += "<blockquote expandable>"
    for i, (user_id, user_data) in enumerate(sorted_24h_users[:10], 1):
        name = user_data['name'] or user_data['username'] or str(user_id)
        text += f"{i}. {name}: {stats['messages_24h']['active_users'][user_id]} 条\n"
    text += "</blockquote>\n"
    if sorted_most_xm_users and any(user_data['xm_count'] > 0 for _, user_data in sorted_most_xm_users):
        text += "\n🍋 羡慕统计:\n"
        text += "<blockquote expandable>"
        for user_id, user_data in sorted_most_xm_users:
            if user_data['xm_count'] > 0:
                name = user_data['name'] or user_data['username'] or str(user_id)
                text += f"{name}: {user_data['xm_count']} 次羡慕\n"
        text += "</blockquote>\n"
    if sorted_most_wocai_users and any(user_data['wocai_count'] > 0 for _, user_data in sorted_most_wocai_users):
        text += "\n🥬 卖菜统计:\n"
        text += "<blockquote expandable>"
        for user_id, user_data in sorted_most_wocai_users:
            if user_data['wocai_count'] > 0:
                name = user_data['name'] or user_data['username'] or str(user_id)
                text += f"{name}: {user_data['wocai_count']} 次卖菜\n"
        text += "</blockquote>\n"

    await stats_message.edit_text(text)