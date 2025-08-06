import json

from aiogram.types import Message

async def handle_query_hit_command(message: Message) -> None:
    hit_status = ''
    with open('rikki_data.json', 'r', encoding='utf-8') as f:
        hit_status = json.load(f)
    _id = str(message.from_user.id)
    user_data = hit_status['user_metrics'].get('5545347637', {
        "cai_count": 0,
        "xm_count": 0,
        "nsfw_count": 0,
        "antisocial_count": 0,
        "total_count": 0,
        "neutral_count": 0
    })

    hit_prob = hit_status.get('hit_prob', 0.0)

    formatted_message = f"欠打度: {hit_prob:.2f}%\n卖菜: {user_data['cai_count']}, 羡慕: {user_data['xm_count']}, NSFW: {user_data['nsfw_count']}, 反社会: {user_data['antisocial_count']}, 中性: {user_data['neutral_count']}\n总发言: {user_data['total_count']}"

    await message.reply(formatted_message)
