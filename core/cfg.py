from aiogram.types import Message

from config import config
from adapters.db.config import update_config_value

async def handle_config_command(message: Message):
    if not message.chat.type in ('group', 'supergroup'):
        await message.reply("此命令只能在群组中使用")
        return
    chat_id = message.chat.id
    group_config = await config.get_group_config(chat_id)
    member = await message.chat.get_member(message.from_user.id)
    is_anonymous = message.sender_chat.id == message.chat.id if message.sender_chat else False
    if not member.status in ('administrator', 'creator') and not is_anonymous:
        await message.reply("只有管理员才能使用此命令")
        return
    splited_text = message.text.split(' ')
    if len(splited_text) == 1:
        lines = []
        for k, v in group_config.items():
            if isinstance(v, dict):
                lines.append(f"{k}:")
                for ik, iv in v.items():
                    lines.append(f"  {ik}: {iv}")
            else:
                lines.append(f"{k}: {v}")
        await message.reply("当前配置：\n" + "\n".join(lines))
        return
    args = splited_text[1:]  # 去掉命令本身
    if len(args) < 2:
        await message.reply("用法： /config \\<key> \\<value>")
        return
    key = args[0]
    if group_config.get(key,None) and not config.is_global_feature_enabled(key):
        await message.reply("该功能已经在全局配置中禁用")
        return
    elif not key in group_config:
        await message.reply("不存在该功能，请检查后重试")
        return
    if key in group_config and isinstance(group_config[key], bool):
        if args[1].lower() in ['true', '1', 'yes', 'on']:
            await update_config_value(chat_id=chat_id, feature=key, key=None,value=True)
            await message.reply(f"功能 {key} 已开启")
        elif args[1].lower() in ['false', '0', 'no', 'off']:
            await update_config_value(chat_id=chat_id, feature=key, key=None,value=False)
            await message.reply(f"功能 {key} 已关闭")
    elif key in group_config and isinstance(group_config[key], dict):
        if args[1].lower() in ['true', '1', 'yes', 'on']:
            await update_config_value(chat_id=chat_id, feature=key, key="enable", value=True)
            await message.reply(f"功能 {key} 已开启")
        elif args[1].lower() in ['false', '0', 'no', 'off']:
            await update_config_value(chat_id=chat_id, feature=key, key="enable", value=False)
            await message.reply(f"功能 {key} 已关闭")
        elif args[1] in group_config[key].keys():
            await update_config_value(chat_id=chat_id, feature=key, key=args[1], value=" ".join(args[2:]))
            await message.reply(f"配置项 {key}.{args[1]} 已更新为 {' '.join(args[2:])}")
        elif args[1] not in group_config[key].keys():
            await message.reply(f"配置项 {key}.{args[1]} 不存在，请检查后重试")
    else:
        await message.reply("指定的配置项不存在，请检查后重试")