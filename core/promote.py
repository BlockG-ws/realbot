from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message
from emoji import is_emoji

from config import config


async def handle_promote_command(message: Message) -> None:
    title = message.text.replace('/t', '').strip()
    if not await config.is_feature_enabled('promote', message.chat.id):
        return
    if message.chat.type not in ['group', 'supergroup']:
        return
    try:
        if not title:
            await message.reply('咱不知道给什么头衔呢')
            return
        else:
            member = await message.chat.get_member(message.reply_to_message.from_user.id if message.reply_to_message else message.from_user.id)
            if len(title) > 16:
                await message.reply('头衔太长了，咱设置不了')
                return
            if any(is_emoji(s) for s in title):
                await message.reply('你这叽里咕噜的杜叔叔也看不懂啊')
                return
            if member.status == 'creator':
                await message.reply('咱不能给群主设置头衔')
                return
            if not member.status in ['administrator','creator']:
                if message.reply_to_message:
                    await message.chat.promote(message.reply_to_message.from_user.id,can_manage_chat=True)
                    await message.chat.set_administrator_custom_title(message.reply_to_message.from_user.id,title)
                    await message.reply(
                        f'{message.from_user.mention_html()} 把 {message.reply_to_message.from_user.mention_html()} 变成了 <b>{title}</b>！',
                        parse_mode='HTML')
                else:
                    await message.chat.promote(message.from_user.id, can_manage_chat=True)
                    await message.chat.set_administrator_custom_title(message.from_user.id, title)
                    await message.reply(
                        f'{message.from_user.mention_html()} 把自己变成了 <b>{title}</b>！',
                        parse_mode='HTML')
            elif member.status == 'administrator' and member.can_be_edited:
                if message.reply_to_message:
                    await message.chat.set_administrator_custom_title(message.reply_to_message.from_user.id,title)
                    await message.reply(
                        f'{message.from_user.mention_html()} 把 {message.reply_to_message.from_user.mention_html()} 变成了 <b>{title}</b>！',
                        parse_mode='HTML')
                else:
                    await message.chat.set_administrator_custom_title(message.from_user.id, title)
                    await message.reply(
                        f'{message.from_user.mention_html()} 把自己变成了 <b>{title}</b>！',
                        parse_mode='HTML')
            else:
                await message.reply('咱不能给这个人设置头衔，可能是因为ta已经被其它管理员设置了头衔')
                return
    except TelegramBadRequest as e:
        await message.reply(f'因为咱没有添加新的管理员的权限，咱没办法设置头衔')
        return
    except Exception as e:
        await message.reply(f'发生了错误: {str(e)}')
        return

