import aiogram.types
from collections import defaultdict
import time

from config import config


class MessageRepeater:
    def __init__(self, message_expiry_seconds=3600):  # 1 hour default
        self.message_counts = defaultdict(lambda: defaultdict(int))
        self.repeated_messages = defaultdict(set)
        self.message_timestamps = defaultdict(lambda: defaultdict(float))
        self.expiry_seconds = message_expiry_seconds

    async def handle_message(self, message: aiogram.types.Message):
        """Handle incoming messages and repeat when a threshold is met"""
        chat_id = message.chat.id
        text = message.text

        if not config.is_feature_enabled('repeater', message.chat.id):
            return

        if not text:
            return

        # Clean expired messages
        self._clean_expired_messages(chat_id)

        # Increment message count
        self.message_counts[chat_id][text] += 1
        self.message_timestamps[chat_id][text] = time.time()

        # If a message appears twice and hasn't been repeated yet
        if (self.message_counts[chat_id][text] >= 2 and
                text not in self.repeated_messages[chat_id]):
            # Mark as repeated and send the message
            self.repeated_messages[chat_id].add(text)
            await message.answer(text)

    def _clean_expired_messages(self, chat_id: int):
        """Remove messages older than expiry_seconds"""
        current_time = time.time()
        expired_messages = []

        for text, timestamp in self.message_timestamps[chat_id].items():
            if current_time - timestamp > self.expiry_seconds:
                expired_messages.append(text)

        for text in expired_messages:
            del self.message_counts[chat_id][text]
            del self.message_timestamps[chat_id][text]
            self.repeated_messages[chat_id].discard(text)