import re

from aiogram.types import Message

from config import config


async def report_broken_links(message: Message):
    if not config.is_feature_enabled('link', message.chat.id):
        return
    # 获取被回复的消息中的链接
    links = []
    # 链接正则表达式
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    text = message.text or message.caption
    # Extract URLs from message text
    if text:
        links = re.findall(url_pattern, text)

    if not links:
        await message.reply("没有找到链接。请提供链接以及希望得到的清理结果。格式最好是 `/report_broken_links 链接 描述文本`。")
        return

    # 处理报告逻辑（例如，保存到数据库或发送给开发者）
    report_content = f"用户 {message.from_user.full_name} ({message.from_user.id}) 报告了以下链接的问题：\n"
    report_content += "\n".join(links) + "\n"
    report_content += f"描述：{text.split(' ')[2] if ' ' in text else text}\n"

    # 将 report_content 发送到开发者
    developer_id = config.get_developer_id()  # 从配置获取开发者ID
    await message.bot.send_message(chat_id=developer_id, text=report_content)

    await message.reply("感谢您的报告，我们会尽快处理！")