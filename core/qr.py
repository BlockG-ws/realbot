import cv2
from aiogram.types import Message, BufferedInputFile
import numpy as np
import zxingcpp

# TODO: add a /qr command
async def parse_qrcode(message: Message) -> None:
    file_id = ""
    if message.photo:
        file_id = message.photo[-1].file_id
    elif message.document and (message.document.mime_type or "").startswith("image/"):
        file_id = message.document.file_id
    else:
        return
    info = await message.bot.get_file(file_id)
    data = await message.bot.download_file(info.file_path)
    file_bytes = np.frombuffer(data.getvalue(), dtype=np.uint8)
    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    content = zxingcpp.read_barcode(image, try_rotate=True, try_downscale=True, try_invert=True)

    if content:
        text = content.text
        if len(text) <= 4000:
            await message.reply(f"解码结果：\n{content.text}",parse_mode=None)
        else:
            file_name = f"{file_id}.txt"
            await message.reply_document(
                BufferedInputFile(text.encode("utf-8"), file_name),
                caption="解码结果过长，已作为文件发送："
            )
