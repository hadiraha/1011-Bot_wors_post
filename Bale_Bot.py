from bale import Bot, Message, Update, InputFile
import os
from dotenv import load_dotenv
import asyncio
import re

# Load environment variables from .env file
load_dotenv()

class BaleBot:
    MAX_MESSAGE_LENGTH = 950  # Safer limit than 1024

    def __init__(self):
        self.token = os.getenv("BALE_API_TOKEN")
        self.chat_id = os.getenv("BALE_CHAT_ID")
        if not self.token or not self.chat_id:
            raise ValueError("BALE_API_TOKEN and BALE_CHAT_ID must be set in .env")
        self.bot = Bot(self.token)
        self.client = Bot(self.token)

        # Continuation messages
        self.continuation_start = "🔄 این پیام ادامه‌ی پیام قبلی است..."
        self.continuation_end = "⏳ ادامه در پیام بعدی..."

    def split_text(self, text, max_length=MAX_MESSAGE_LENGTH):
        """
        Splits text into smaller chunks, ensuring words are not broken.
        Adds continuation markers when messages are split.
        """
        if len(text) <= max_length:
            return [text]

        chunks = []
        words = text.split(" ")
        current_chunk = ""

        for word in words:
            if len(current_chunk) + len(word) + 1 > max_length:
                chunks.append(current_chunk.strip() + f"\n\n{self.continuation_end}")
                current_chunk = f"{self.continuation_start}\n\n{word}"  # Start new chunk
            else:
                current_chunk += " " + word

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    async def run(self, text, photo_path=None):
        """
        Handles sending messages, ensuring long texts are split properly.
        """
        async with self.client as bot:
            try:
                print(f"Running with text: {text[:30]}...")
                chunks = self.split_text(text)
                
                for chunk in chunks:
                    print(f"Sending chunk: {chunk[:30]}...")
                    if photo_path:
                        await self.send_photo_with_caption(bot, chunk, photo_path)
                    else:
                        await self.send_text_message(bot, chunk)
                    await asyncio.sleep(1)  # Avoid sending too fast

            except Exception as e:
                print(f"Error sending message: {e}")

    async def send_text_message(self, bot, text):
        """
        Sends a text message with flood control handling.
        """
        try:
            print(f"Sending text message: {text[:30]}...")
            await bot.send_message(chat_id=self.chat_id, text=text)
        except Exception as e:
            if "Retry in" in str(e):
                retry_after = self._parse_retry_time(str(e))
                print(f"Flood control exceeded. Retrying in {retry_after} seconds...")
                await asyncio.sleep(retry_after)
                await bot.send_message(chat_id=self.chat_id, text=text)
            else:
                print(f"Error sending message: {e}")

    async def send_photo_with_caption(self, bot, text, photo_path):
        """
        Sends a photo with a caption, handling long captions properly.
        """
        try:
            print(f"Sending photo with caption: {text[:30]}...")
            photo_path = os.path.abspath(photo_path)

            if not os.path.exists(photo_path):
                print(f"Error: File not found at {photo_path}")
                return
            if not os.access(photo_path, os.R_OK):
                print(f"Error: File not readable at {photo_path}")
                return

            valid_extensions = (".jpg", ".jpeg", ".png", ".gif")
            if not photo_path.lower().endswith(valid_extensions):
                print(f"Error: Invalid file extension for {photo_path}")
                return

            chunks = self.split_text(text, max_length=1024)  # Adjust caption length

            with open(photo_path, 'rb') as f:
                photo = InputFile(f.read())
                await bot.send_photo(chat_id=self.chat_id, photo=photo, caption=chunks[0])

            for chunk in chunks[1:]:
                await self.send_text_message(bot, chunk)

        except Exception as e:
            if "Retry in" in str(e):
                retry_after = self._parse_retry_time(str(e))
                print(f"Flood control exceeded. Retrying in {retry_after} seconds...")
                await asyncio.sleep(retry_after)
                await self.send_photo_with_caption(bot, text, photo_path)
            else:
                print(f"Error sending photo: {e}")

    def _parse_retry_time(self, error_str):
        """
        Extracts the retry time from the error string.
        """
        match = re.search(r"Retry in (\d+)", error_str)
        return int(match.group(1)) if match else 0

    async def send_batch_messages(self, messages, batch_size=5, delay=1):
        """
        Sends messages in batches to prevent spamming and handles flood control.
        """
        async with self.client as bot:
            for i in range(0, len(messages), batch_size):
                batch = messages[i:i + batch_size]
                for message in batch:
                    text = message.get("text", "")
                    photo_path = message.get("photo")
                    print(f"Sending batch {i//batch_size + 1}/{len(messages)//batch_size + 1}...")

                    try:
                        await self.run(text, photo_path)
                        print(f"Message sent: {text[:30]}...")
                        await asyncio.sleep(delay)  # Add a delay between messages
                    except Exception as e:
                        if 'Retry in' in str(e):
                            retry_after = int(str(e).split('Retry in ')[1].split(' ')[0])
                            print(f"Flood control exceeded. Retrying in {retry_after} seconds...")
                            await asyncio.sleep(retry_after)
                            await self.run(text, photo_path)
                        else:
                            print(f"Error sending message: {e}")