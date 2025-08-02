from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import Router

from config import config
from mastodon import Mastodon

router = Router()

class AuthStates(StatesGroup):
    waiting_for_token = State()

def check_client_cred_exists(instance: str) -> bool:
    """
    检查实例的凭据文件是否存在
    """
    try:
        with open(f'secrets/realbot_{instance}_clientcred.secret', 'r'):
            return True
    except FileNotFoundError:
        return False

def check_user_cred_exists(instance: str, userid: int) -> bool:
    """
    检查用户凭据文件是否存在
    """
    try:
        with open(f'secrets/realbot_{instance}_{userid}_usercred.secret', 'r'):
            return True
    except FileNotFoundError:
        return False

async def handle_token(instance,mastodon, message: Message):
    mastodon.log_in(
        code=message.text,
        to_file=f"secrets/realbot_{instance}_{message.from_user.id}_usercred.secret",
        scopes=['read:accounts', 'read:statuses', 'write:media', 'write:statuses']
    )

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
    if not check_client_cred_exists(instance):
        Mastodon.create_app(
            'realbot',
            api_base_url='https://{}'.format(instance),
            to_file='secrets/realbot_{}_clientcred.secret'.format(instance),
            scopes=['read:accounts', 'read:statuses','write:media','write:statuses']
        )
    mastodon = Mastodon(client_id=f'secrets/realbot_{instance}_clientcred.secret', )
    auth_url = mastodon.auth_request_url()
    await message.reply('请在浏览器中打开链接进行身份验证：\n{}\n验证完成后，请用得到的 token 回复这条消息'.format(auth_url))
    # 在发送消息后设置状态
    await state.update_data(instance=instance)
    await state.set_state(AuthStates.waiting_for_token)

# 创建处理回复的 handler
@router.message(AuthStates.waiting_for_token)
async def handle_token_reply(message: Message, state: FSMContext):
    data = await state.get_data()
    instance = data.get('instance')
    mastodon = Mastodon(client_id=f'secrets/realbot_{instance}_clientcred.secret')
    status = await message.reply('正在处理身份验证，请稍候...')
    await handle_token(instance,mastodon,message)
    await status.edit_text('身份验证成功！\n现在你可以使用 /post 命令将消息发布到联邦网络。')
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
    import os
    import glob

    user_cred_pattern = f'secrets/realbot_*_{user_id}_usercred.secret'
    user_cred_files = glob.glob(user_cred_pattern)

    if not user_cred_files:
        await message.reply('请先使用 /fauth 命令进行身份验证')
        return

    # 从文件名中提取实例名
    cred_file = user_cred_files[0]  # 假设用户只绑定一个实例
    filename = os.path.basename(cred_file)
    # 格式: realbot_{instance}_{userid}_usercred.secret
    parts = filename.split('_')
    instance = '_'.join(parts[1:-2])  # 提取实例名部分

    mastodon = Mastodon(
        access_token=f'{cred_file}',
        api_base_url=f'https://{instance}'
    )

    # 发布消息到联邦网络
    try:
        arguments = message.text.replace('/post', '', 1).strip().split(' ')
        if len(arguments) >= 1 and arguments[0]:
            visibility = arguments[0]  # 默认可见性为账号设置的可见性
        else:
            visibility = None

        status_message = await message.reply('尝试发布消息到联邦网络...')
        # 处理图片附件
        media_ids = []
        if message.reply_to_message.photo:
            await status_message.edit_text('正在处理图片附件...')
            # 获取最大尺寸的图片
            photo = message.reply_to_message.photo[-1]
            file_info = await message.bot.get_file(photo.file_id)
            file_data = await message.bot.download_file(file_info.file_path)

            # 上传图片到Mastodon
            media = mastodon.media_post(file_data, mime_type='image/png')
            media_ids.append(media['id'])
        text = message.reply_to_message.text
        if media_ids:
            text = message.reply_to_message.caption
        # 发布消息
        status = mastodon.status_post(
            text,
            media_ids=media_ids if media_ids else None,
            visibility = visibility
        )
        status_url = status['url']
        await status_message.edit_text(f'消息已成功发布到联邦网络！\n{status_url}')
    except Exception as e:
        await message.reply(f'发布失败: {str(e)}')