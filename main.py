import asyncio
from extract_content import DocxParser
from telegram_bot import TelegramBot
from Bale_Bot import BaleBot
import os

async def main():
    # Path to the Word document
    file_path = input("Enter the path to your Word document: ").strip()

    # Extract content and images
    print("Extracting content and images from the Word document...")
    try:
        parser = DocxParser(file_path)
        content_with_images = parser.extract_headings_content_with_images()
    except Exception as e:
        print(f"Error extracting content: {e}")
        return

    # Send to Telegram
    print("Sending content and images to Telegram...")
    try:
        bot = TelegramBot()
        for section in content_with_images:
            await bot.send_message_with_images(section['text'], section['images'])
        print("All content and images sent successfully to Telegram!")
    except Exception as e:
        print(f"Error sending messages to Telegram: {e}")

    # Send content to Bale
    print("Sending content and images to Bale...")
    try:
        bale_bot = BaleBot()
        for section in content_with_images:
            text = section["text"]
            images = section.get("images", [])

            if images:
                # Send text and all associated images
                for image in images:
                    # Validate image path
                    image_path = os.path.abspath(image)
                    if not os.path.exists(image_path):
                        print(f"Error: Image not found at {image_path}")
                        continue
                    if not os.access(image_path, os.R_OK):
                        print(f"Error: Image not readable at {image_path}")
                        continue
                    
                    print(f"Sending text: {text} with image: {image_path}")
                    await bale_bot.run(text, photo_path=image_path)

                    # Clear the text after the first image to avoid duplicate captions
                    text = ""
            else:
                # Send text-only message if no images are available
                print(f"Sending text-only: {text}")
                await bale_bot.run(text)

        print("All content and images sent successfully to Bale!")
    except Exception as e:
        print(f"Error sending messages to Bale: {e}")


if __name__ == "__main__":
    asyncio.run(main())
    