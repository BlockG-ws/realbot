import json
import logging
import uuid

import aiohttp
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import Router

from adapters.db.fedi import get_fedi_user_cred, update_fedi_user_cred, get_fedi_client_info, update_fedi_client_info, \
    get_fedi_user_instance_domains, fedi_instance_is_misskey
from config import config
from mastodon import Mastodon

router = Router()

class AuthStates(StatesGroup):
    waiting_for_token = State()


async def check_client_cred_exists(instance: str) -> bool:
    client_id = (await get_fedi_client_info(instance)).get('client_id', '')
    client_secret = (await get_fedi_client_info(instance)).get('client_secret', '')
    if client_id and client_secret:
        return True
    else:
        return False

async def instance_is_misskey(instance: str) -> bool:
    """
    检查实例是否是 Misskey 实例
    """
    is_misskey = await fedi_instance_is_misskey(instance)
    if isinstance(is_misskey, bool):
        return is_misskey
    # 如果数据库中没有记录，则通过请求实例信息来判断
    else:
        try:
            async with aiohttp.ClientSession() as client:
                # 获取实例的 NodeInfo 信息，以确定其软件类型
                async with client.get(f"https://{instance}/.well-known/nodeinfo", headers={"Content-Type": "application/json"},
                                       allow_redirects=False) as r:
                    nodeinfo_path = (await r.json()).get('links', [])[0].get('href', '')
                async with client.get(nodeinfo_path, headers={"Content-Type": "application/json"},
                                       allow_redirects=False) as r:
                    data = await r.json()
                    software_name = data.get('software', {}).get('name', '').lower()
                    if software_name in ['misskey', 'sharkey', 'firefish']:
                        await update_fedi_client_info(instance, True, '', '')
                        return True
                    else:
                        await update_fedi_client_info(instance, False, '', '')
                        return False  # 如果不是，则不是 Misskey 实例
        except Exception as e:
            logging.debug(f"检查实例 {instance} 是否为 Misskey 时发生错误: {e}")
            return False

async def handle_token(instance, mastodon, message: Message):
    access_token = mastodon.log_in(
        code=message.text,
        scopes=['read:accounts', 'read:statuses', 'write:media', 'write:statuses'],
        redirect_uri='urn:ietf:wg:oauth:2.0:oob'
    )
    # 保存用户凭据
    await update_fedi_user_cred(instance, message.from_user.id, access_token)

async def handle_auth(message: Message, state: FSMContext):
    """
    处理身份验证
    """
    if not config.is_feature_enabled('fedi', message.chat.id):
        return
    if not message.chat.type == 'private':
        await message.reply('请在私聊中使用此命令')
        return
    instance = message.text.replace('/fauth', '').strip()
    if instance == '':
        await message.reply('请输入实例域名，例如：`example.com`')
        return
    auth_url = ''
    session_id = uuid.uuid4()
    if not await instance_is_misskey(instance):
        # 如果是 Mastodon 实例，检查客户端凭据是否存在
        if not await check_client_cred_exists(instance):
            try:
                client_id, client_secret = Mastodon.create_app(
                    'realbot',
                    api_base_url='https://{}'.format(instance),
                    scopes=['read:accounts', 'read:statuses','write:media','write:statuses']
                )
                await update_fedi_client_info(instance, False, client_id, client_secret)
            except Exception as e:
                logging.warning(e)
                await message.reply(f'创建应用失败：{str(e)}\n请确保实例域名正确并且实例支持 Mastodon API。')
                return
        client_id = (await get_fedi_client_info(instance))['client_id']
        client_secret = (await get_fedi_client_info(instance))['client_secret']
        mastodon = Mastodon(client_id,client_secret,api_base_url='https://{}'.format(instance))
        auth_url = mastodon.auth_request_url()
    else:
        # 如果是 Misskey 实例，使用不同的创建应用方式
        try:
            auth_url = f'https://{instance}/miauth/{session_id}?name=realbot&permission=read:account,write:notes,write:drive'
        except Exception as e:
            logging.warning(e)
            await message.reply(f'创建应用失败：{str(e)}\n请确保实例域名正确并且实例支持 Misskey API。')
            return

    await message.reply('请在浏览器中打开链接进行身份验证：\n{}\n验证完成后，请用得到的 token 回复这条消息。\n注意：对于使用 Akkoma 的用户，可能需要验证两次。对于使用 misskey 的用户，请任意输入文本。'.format(auth_url))
    # 在发送消息后设置状态
    await state.update_data(instance=instance,session=session_id)
    await state.set_state(AuthStates.waiting_for_token)

# 创建处理回复的 handler
@router.message(AuthStates.waiting_for_token)
async def handle_token_reply(message: Message, state: FSMContext):
    data = await state.get_data()
    instance = data.get('instance')
    session_id = data.get('session')
    if not await instance_is_misskey(instance):
        client_id = (await get_fedi_client_info(instance))['client_id']
        client_secret = (await get_fedi_client_info(instance))['client_secret']
        mastodon = Mastodon(client_id,client_secret,api_base_url='https://{}'.format(instance))
        status = await message.reply('正在处理身份验证，请稍候...')
        try:
            await handle_token(instance,mastodon,message)
            await status.edit_text('身份验证成功！\n现在你可以使用 /post 命令将消息发布到联邦网络。')
        except Exception as e:
            logging.warning('Error during Mastodon auth:', exc_info=e)
            await status.edit_text('身份验证失败，请确保实例域名正确并且实例支持 Mastodon API。\n错误信息: {}'.format(str(e)))
    else:
        status = await message.reply('正在处理身份验证，请稍候...')
        misskey_check_url = f'https://{instance}/api/miauth/{session_id}/check'
        async with aiohttp.ClientSession() as client:
            async with client.post(misskey_check_url, data="", headers={"Accept":"*/*"},allow_redirects=False) as r:
                if r.status == 200:
                    data = await r.json()
                    token = data.get('token','')
                    if token:
                        # 保存用户凭据
                        await update_fedi_user_cred(instance, message.from_user.id, token)
                        await status.edit_text('身份验证成功！\n现在你可以使用 /post 命令将消息发布到联邦网络。')
                else:
                    await status.edit_text('身份验证失败，请确保实例域名正确并且实例支持 Misskey API。\n以下的信息可能有助于诊断问题：\n{}'.format(await r.text()))
    # 清除状态
    await state.clear()

async def handle_post_to_fedi(message: Message):
    """
    处理发布到联邦网络的消息
    """
    if not config.is_feature_enabled('fedi', message.chat.id):
        return
    if not message.reply_to_message:
        await message.reply('请回复要发布的消息')
        return

    user_id = message.from_user.id

    # 查找用户绑定的实例
    user_creds = await get_fedi_user_instance_domains(user_id)
    if not user_creds:
        await message.reply('请先使用 /fauth 命令进行身份验证')
        return
    arguments = message.text.replace('/post', '', 1).strip().split(' ')
    specified_instance = None
    visibility = None
    if len(arguments) >= 1 and arguments[0]:
        # 检查第一个参数是否是实例名
        first_arg = arguments[0]
        # 检查是否存在对应的凭据文件
        matching_creds = await get_fedi_user_cred(first_arg, user_id)
        if matching_creds:
            specified_instance = first_arg
            if len(arguments) >= 2:
                visibility = arguments[1]
        else:
            visibility = arguments[0]
    # 如果指定了实例，使用指定的实例
    if specified_instance:
        instance = specified_instance
    else:
        # 如果有多个实例，让用户选择
        if user_creds and len(user_creds) > 1:
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

            # 提取所有实例名
            instances = []
            for cred in user_creds:
                instances.append(cred)


            # 创建选择按钮
            keyboard = []
            for instance_name in instances:
                keyboard.append([InlineKeyboardButton(
                    text=f"{instance_name}",
                    callback_data=f"post:{instance_name}:"
                )])

            # 添加全部发送选项
            keyboard.append([InlineKeyboardButton(
                text="发送到所有实例",
                callback_data="post_instance:all"
            )])

            reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
            await message.reply("请选择要发送到的实例：\n（实验性，目前还不能使用）", reply_markup=reply_markup)
            return
        else:
            # 只有一个实例，直接使用
            instance = user_creds[0]

    access_token = await get_fedi_user_cred(instance, user_id)
    client_id = (await get_fedi_client_info(instance))['client_id']
    client_secret = (await get_fedi_client_info(instance))['client_secret']
    mastodon = Mastodon(
        access_token=access_token,
        client_id=client_id,client_secret=client_secret,
        api_base_url=f'https://{instance}'
    )

    # 发布消息到联邦网络
    try:
        status_message = await message.reply('尝试发布消息到联邦网络...')
        is_misskey = await instance_is_misskey(instance)
        # 处理图片附件
        media_ids = []
        if message.reply_to_message.photo:
            await status_message.edit_text('正在处理图片附件...')
            # 获取最大尺寸的图片
            photo = message.reply_to_message.photo[-1]
            file_info = await message.bot.get_file(photo.file_id)
            file_data = await message.bot.download_file(file_info.file_path)
            if not is_misskey:
                # 上传图片到Mastodon
                media = mastodon.media_post(file_data, mime_type='image/png')
                media_ids.append(media['id'])
            else:
                misskey_upload_drive_url = f"https://{instance}/api/drive/files/create"
                token = access_token

                file_info = await message.bot.get_file(photo.file_id)
                file_data = await message.bot.download_file(file_info.file_path)

                data = aiohttp.FormData()
                data.add_field('i',token)
                data.add_field('file', file_data, filename=f"{photo.file_id}.png", content_type='image/png')
                #if photo.has_media_spoiler:
                #    data.add_field('isSensitive', True)
                data.add_field('name', f"tg_{photo.file_id}.png")
                async with aiohttp.ClientSession() as client:
                    async with client.post(misskey_upload_drive_url, allow_redirects=False, data=data) as r:
                        if r.status == 200:
                            media_info = await r.json()
                            media_ids.append(media_info['id'])
                        else:
                            await status_message.reply(f'上传图片失败，但是仍然可以发布这条消息的文本部分。\n错误信息: {r.status} {await r.text()}')
        # 如果有图片附件而且图片有 caption，优先使用图片的 caption 作为文本
        text = message.reply_to_message.caption or message.reply_to_message.text
        if not is_misskey:
            status = mastodon.status_post(
                text,
                media_ids=media_ids if media_ids else None,
                visibility = visibility
            )
            status_url = status['url']
            await status_message.edit_text(f'消息已成功发布到联邦网络！\n{status_url}')
        else:
            # 对于 Misskey 实例，使用不同的发布方式
            misskey_create_status_url = f'https://{instance}/api/notes/create'
            token = access_token
            data = {}
            if token and media_ids:
                data = json.dumps({
                    "visibility": visibility if visibility else "public",
                    "text": text,
                    "fileIds": media_ids
                })
            elif token:
                data = json.dumps({
                    "visibility": visibility if visibility else "public",
                    "text": text
                })
            created_note = {}
            async with aiohttp.ClientSession() as client:
                async with client.post(misskey_create_status_url, allow_redirects=False, data=data,headers={"Authorization": f"Bearer {token}","Content-Type": "application/json"}) as r:
                    if r.status == 200:
                        created_note = await r.json()
                    else:
                        await status_message.edit_text(f'发布失败: {r.status} - {await r.text()}')
                        return
            status_url = f'https://{instance}/notes/{created_note["createdNote"]["id"]}'
            await status_message.edit_text(f'消息已成功发布到联邦网络！\n{status_url}')
    except Exception as e:
        logging.warning('Error posting to fedi:', exc_info=e)
        await status_message.edit_text(f'发布失败: {str(e)}')


@router.callback_query(lambda c: c.data.startswith('post:'))
async def handle_instance_selection(callback: CallbackQuery):
    """处理实例选择回调"""
    await callback.answer()

    data_parts = callback.data.split(':')

    selected_instance = data_parts[1]

    # 获取原始回复消息
    # 获取原始 /post 命令消息，然后获取它回复的消息
    post_command_message = callback.message.reply_to_message
    original_message = post_command_message.reply_to_message if post_command_message else None
    if not original_message:
        await callback.message.edit_text("错误：找不到原始消息")
        return

    user_id = callback.from_user.id

    mastodon = Mastodon(
        access_token=await get_fedi_user_cred(selected_instance, user_id),
        client_id=(await get_fedi_client_info(selected_instance))['client_id'],
        client_secret=(await get_fedi_client_info(selected_instance))['client_secret'],
        api_base_url=f'https://{selected_instance}'
    )

    # 发布消息到联邦网络
    try:
        status_message = await original_message.reply('尝试发布消息到联邦网络...')
        # 处理图片附件
        media_ids = []
        cb_arguments = original_message.text.replace('/post', '', 1).strip().split(' ')
        if not original_message.reply_to_message:
            await status_message.edit_text("错误：找不到要发布的消息")
            return

        if original_message.reply_to_message.photo:
            await status_message.edit_text('正在处理图片附件...')
            # 获取最大尺寸的图片
            photo = original_message.reply_to_message.photo[-1]
            file_info = await callback.message.bot.get_file(photo.file_id)
            file_data = await callback.message.bot.download_file(file_info.file_path)

            # 上传图片到Mastodon
            media = mastodon.media_post(file_data, mime_type='image/png')
            media_ids.append(media['id'])
        text = original_message.reply_to_message.text
        if media_ids:
            text = original_message.reply_to_message.caption
        # 发布消息
        status = mastodon.status_post(
            text,
            media_ids=media_ids if media_ids else None,
            visibility = cb_arguments[0] if len(cb_arguments) == 1 else None  # 默认为账户默认可见性
        )
        status_url = status['url']
        await status_message.edit_text(f'消息已成功发布到联邦网络！\n{status_url}')
        await callback.message.delete()
    except Exception as e:
        await status_message.edit_text(f'发布失败: {str(e)}')
