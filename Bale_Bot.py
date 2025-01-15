from bale import Bot, Message, Update, InputFile
import os
from dotenv import load_dotenv
import asyncio
import re

# Load environment variables from .env file
load_dotenv()

class BaleBot:
    def __init__(self):
        """
        Initialize the Bale bot with API credentials from the environment variables.
        """
        self.token = os.getenv("BALE_API_TOKEN")
        self.chat_id = os.getenv("BALE_CHAT_ID")
        if not self.token or not self.chat_id:
            raise ValueError("BALE_API_TOKEN and BALE_CHAT_ID must be set in .env")
        self.bot = Bot(self.token)
        self.client = Bot(self.token)

    async def run(self, text, photo_path=None):
        async with self.client as bot:
            try:
                print(f"Running with text: {text[:30]}...")
                # Split text into chunks if it's too long
                if len(text) > 1024:  # Adjust max length as per the platform's limits
                    chunks = self.split_text(text)
                    for chunk in chunks:
                        print(f"Sending chunk of text: {chunk[:30]}...")
                        if photo_path:
                            # Send image with each chunk of text as the caption
                            await self.send_photo_with_caption(bot, chunk, photo_path)
                        else:
                            # Send text-only chunk
                            await self.send_text_message(bot, chunk)
                        await asyncio.sleep(1)  # Add delay between chunks
                else:
                    if photo_path:
                        # Send the image with caption
                        await self.send_photo_with_caption(bot, text, photo_path)
                    else:
                        # Send Text only
                        await self.send_text_message(bot, text)

            except Exception as e:
                print(f"Error sending message: {e}")

    def split_text(self, text, max_length=1024):
        """
        Split long text into smaller chunks to avoid message size limit.
        """
        return [text[i:i + max_length] for i in range(0, len(text), max_length)]

    async def send_text_message(self, bot, text):
        """
        Sends a text message and handles flood control.
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
        Sends a photo with caption and handles flood control.
        """
        try:
            print(f"Sending photo with caption: {text[:30]}...")
            photo_path = os.path.abspath(photo_path)  # Resolve to absolute path
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

            with open(photo_path, 'rb') as f:
                photo = InputFile(f.read())
                await bot.send_photo(chat_id=self.chat_id, photo=photo, caption=text)
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
        Extract the retry time from the error string.
        """
        match = re.search(r"Retry in (\d+)", error_str)
        return int(match.group(1)) if match else 0

    async def send_batch_messages(self, messages, batch_size=5, delay=1):
        """
        Sends messages in batches to avoid spamming too many messages.
        Introduces a delay between messages and handles flood control.
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

    # async def send_message(self, text, photo_path=None):
    #     """
    #     Sends a message or a message with an image to the specified Bale chat or channel.
    #     If photo_path is provided, sends the image along with the text as a caption.
    #     """
    #     async with self.client as bot:
    #         try:
    #             if photo_path:
    #                 # Send the image with a caption
    #                 with open(photo_path, "rb") as photo:
    #                     await bot.send_photo(chat_id=self.chat_id, photo=photo, caption=text)
    #             else:
    #                 # Send text-only message
    #                 await bot.send_message(chat_id=self.chat_id, text=text)
    #         except Exception as e:
    #             print(f"Error sending message: {e}")
# Test
# if __name__ == "__main__":
#     async def main():
#         bale_bot = BaleBot()
#         test_image_path = r"extracted_images\image_1.png"  # Replace with a valid image path
#         messages = [
#             {"text": "Test Message 1 - Text Only"},
#             {"text": "Test Message 2 - With Image", "photo": test_image_path if os.path.exists(test_image_path) else None},
#             {"text": "Test Message 3 - Text Only"},
#         ]
#         try:
#             await bale_bot.send_batch_messages(messages)
#             print("All messages sent successfully to Bale.")
#         except Exception as e:
#             print(f"An error occurred while sending messages to Bale: {e}")

#     asyncio.run(main())
