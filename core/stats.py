from aiogram.types import Message

from config import config


async def handle_stats_command(message: Message):
    """处理统计命令"""
    if not await config.is_feature_enabled('stats', message.chat.id):
        return
    if message.chat.type not in ['group', 'supergroup']:
        await message.reply("此命令仅在群组中可用")
        return
    from adapters.db.stats import get_group_stats
    stats = await get_group_stats(message.chat.id)

    if not stats:
        await message.reply("暂无统计数据")
        return

    stats_message = await message.reply("正在生成统计信息...")
    user_stats = stats.users or {}
    message_24h_stats = stats.messages_24h or {}
    # 按消息数量排序用户
    sorted_users = sorted(
        user_stats.items(),
        key=lambda x: x[1]['message_count'],
        reverse=True
    )
    active = message_24h_stats.get('active_users', {})
    sorted_24h_users = sorted(
        [
            (user_id, user_stats.get(user_id) or user_stats.get(int(user_id), {}))
            for user_id in active.keys()
        ],
        key=lambda x: active.get(x[0], 0),
        reverse=True
    )
    sorted_most_xm_users = sorted(
        user_stats.items(),
        key=lambda x: x[1].get('xm_count',0),
        reverse=True
    )
    sorted_most_wocai_users = sorted(
        user_stats.items(),
        key=lambda x: x[1].get('wocai_count',0),
        reverse=True
    )


    # 构建统计消息
    text = f"📊 群组统计\n\n"
    text += f"总消息数: {stats.total_messages}\n"
    text += f"24小时内消息数: {message_24h_stats['message_count']}\n"
    text += f"活跃用户数: {len(user_stats)}\n"
    text += f"24小时内活跃用户数:{len(message_24h_stats['active_users'])}\n\n"
    text += "🏆 发言排行榜:\n"
    text += "<blockquote expandable>"
    for i, (user_id, user_data) in enumerate(sorted_users[:10], 1):
        name = user_data['name'] or user_data['username'] or str(user_id)
        text += f"{i}. {name}: {user_data['message_count']} 条\n"
    text += "</blockquote>\n\n"
    text += "📈 24小时内发言排行榜:\n"
    text += "<blockquote expandable>"
    for i, (user_id, user_data) in enumerate(sorted_24h_users[:10], 1):
        name = user_data['name'] or user_data['username'] or str(user_id)
        text += f"{i}. {name}: {message_24h_stats['active_users'][user_id]} 条\n"
    text += "</blockquote>\n\n"
    if sorted_most_xm_users and any(user_data['xm_count'] > 0 for _, user_data in sorted_most_xm_users):
        text += "\n🍋 羡慕统计:\n"
        text += "<blockquote expandable>"
        for user_id, user_data in sorted_most_xm_users:
            if user_data.get('xm_count',0) > 0:
                name = user_data['name'] or user_data['username'] or str(user_id)
                text += f"{name}: {user_data['xm_count']} 次羡慕\n"
        text += "</blockquote>\n\n"
    if sorted_most_wocai_users and any(user_data['wocai_count'] > 0 for _, user_data in sorted_most_wocai_users):
        text += "\n🥬 卖菜统计:\n"
        text += "<blockquote expandable>"
        for user_id, user_data in sorted_most_wocai_users:
            if user_data.get('wocai_count',0) > 0:
                name = user_data['name'] or user_data['username'] or str(user_id)
                text += f"{name}: {user_data['wocai_count']} 次卖菜\n"
        text += "</blockquote>\n"

    await stats_message.edit_text(text)