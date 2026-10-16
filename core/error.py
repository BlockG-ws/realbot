import logging
import time
import traceback

from aiogram import Bot
from aiogram.types import Message, ErrorEvent, Update, BufferedInputFile
from aiogram.utils.text_decorations import html_decoration

from config import config


async def handle_error(event: ErrorEvent, bot: Bot) -> None:
    er = await config.get_feature_config("error")
    target_chat_id = er.get("chat_id")
    target_topic_id = er.get("topic_id")

    if not target_chat_id:
        admin_id = await config.get_admin_id()
        if not admin_id:
            return
        target_chat_id = admin_id


    try:
        e = event.exception
        e_type = type(e).__name__
        e_msg = str(e)
        tb = "\n".join(traceback.format_exception(type(e), e, e.__traceback__))

        def _get_update_info(update: Update):
            if not update:
                return
            info = { "id": update.update_id }
            if update.message:
                info["type"] = "message"
                msg = update.message
                info["chat_info"] = msg.chat.title or msg.chat.username or str(msg.chat.id)
                info["user_info"] = msg.from_user.full_name if msg.from_user else "unknown"
                if msg.text:
                    info["text"] = msg.text
            elif update.callback_query:
                info["type"] = "callback_query"
                callback = update.callback_query
                info["data"] = callback.data
            return info

        context = _get_update_info(event.update)
        send_args = {
            "chat_id": target_chat_id,
            "message_thread_id": target_topic_id if target_topic_id else None
        }

        report = (
            "==== REALBOT REPORT ====\n"
            f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Context:\n{context}\n"
            f"Exception: {e_type}: {e_msg}\n\n"
            f"{tb}"
        )

        if len(report) > 2000:
            filename = f"error_{int(time.time())}_{e_type}.txt"
            document = BufferedInputFile(
                file=report.encode("utf-8"),
                filename=filename,
            )
            caption = (
                f"<b>Bot 运行时发生异常，由于消息过长，已将其转为文件发送。</b>\n这些错误不影响 bot 的正常运行，但如果您正在运行自己的 realbot 实例，这些错误仍然值得注意。您可以查看文件，或前往 bot 控制台获得更多信息。\n"
            )
            await bot.send_document(document=document, caption=caption, **send_args)
        else:
            # 短错误：直接文本发送
            text = (
                f"<b>Bot 运行时发生异常</b>\n"
                f"<b>来源:</b> <code>{html_decoration.quote(context)}</code>\n"
                f"<b>类型:</b> <code>{html_decoration.quote(e_type)}</code>\n"
                f"<b>信息:</b> <code>{html_decoration.quote(e_msg)}</code>\n\n"
                f"<pre><code class=\"language-python\">{html_decoration.quote(tb)}</code></pre>"
            )
            await bot.send_message(text=text, **send_args)
    except Exception as inner_e:
        # 防止错误处理器自身发送失败导致死循环或未捕获崩溃
        logging.error(f"Failed to report error to Telegram: {inner_e}")


