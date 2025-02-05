import asyncio
from telegram import Bot, InputFile
import os
from dotenv import load_dotenv
import re

load_dotenv()

class TelegramBot:
    MAX_CAPTION_LENGTH = 1024  # Telegram's caption character limit
    MAX_MESSAGE_LENGTH = 4000  # Safer limit than 4096

    def __init__(self, continuation_notation=None):
        self.token = os.getenv("TELEGRAM_API_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if not self.token or not self.chat_id:
            raise ValueError("TELEGRAM_API_TOKEN and TELEGRAM_CHAT_ID must be set in .env")
        self.bot = Bot(token=self.token)

        # Default continuation messages if not provided
       
       
        self.continuation_end = continuation_notation or "⏳ ادامه در پیام بعدی..."

    def split_text(self, text, max_length):
        """
        Splits a given text into chunks, ensuring that words are not broken.
        Adds continuation messages where necessary.
        """
        if len(text) <= max_length:
            return [text]

        chunks = []
        words = text.split(" ")
        current_chunk = ""

        for word in words:
            # If adding the next word exceeds the limit, finalize the current chunk
            if len(current_chunk) + len(word) + 1 > max_length:
                chunks.append(current_chunk.strip() + f"\n\n{self.continuation_end}")
                current_chunk = f"{self.continuation_start}\n\n{word}"  # Start new chunk
            else:
                current_chunk += " " + word

        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    async def send_message(self, text, photo_path=None):
        """
        Sends a message or a message with an image to the specified Telegram chat or channel.
        Implements flood control handling.
        """
        try:
            if photo_path:
                chunks = self.split_text(text, self.MAX_CAPTION_LENGTH)
                with open(photo_path, 'rb') as photo:
                    await self._safe_send_photo(photo, chunks[0])  # First chunk with the image
                    for chunk in chunks[1:]:
                        await self._safe_send_message(chunk)
            else:
                chunks = self.split_text(text, self.MAX_MESSAGE_LENGTH)
                for chunk in chunks:
                    await self._safe_send_message(chunk)
        except Exception as e:
            print(f"Error sending message: {e}")

    async def send_message_with_images(self, text, images):
        """
        Sends all associated images with their text as a caption to Telegram.
        If there are no images, only sends the text. Handles flood control.
        """
        if not images:
            await self.send_message(text)
        else:
            for image in images:
                with open(image, "rb") as img_file:
                    try:
                        chunks = self.split_text(text, self.MAX_CAPTION_LENGTH)
                        await self._safe_send_photo(img_file, chunks[0])  # Send first chunk as caption
                        for chunk in chunks[1:]:
                            await self._safe_send_message(chunk)
                        text = ""  # Clear caption after first image
                    except Exception as e:
                        print(f"Error sending image with caption: {e}")

    async def _safe_send_message(self, text):
        """
        Sends a text message with flood control handling.
        """
        while True:
            try:
                await self.bot.send_message(chat_id=self.chat_id, text=text)
                break  # Exit loop if successful
            except Exception as e:
                if "Retry in" in str(e):
                    retry_after = self._parse_retry_time(str(e))
                    print(f"Flood control exceeded. Retrying in {retry_after} seconds...")
                    await asyncio.sleep(retry_after)
                else:
                    raise e

    async def _safe_send_photo(self, photo, caption):
        """
        Sends a photo with caption and handles flood control.
        """
        while True:
            try:
                await self.bot.send_photo(chat_id=self.chat_id, photo=photo, caption=caption)
                break  # Exit loop if successful
            except Exception as e:
                if "Retry in" in str(e):
                    retry_after = self._parse_retry_time(str(e))
                    print(f"Flood control exceeded. Retrying in {retry_after} seconds...")
                    await asyncio.sleep(retry_after)
                else:
                    raise e

    def _parse_retry_time(self, error_message):
        """
        Extracts the retry time from the error message.
        """
        match = re.search(r"Retry in (\d+) seconds", error_message)
        if match:
            return int(match.group(1))
        return 5  # Default to 5 seconds if parsing fails