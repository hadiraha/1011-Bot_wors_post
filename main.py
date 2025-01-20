import asyncio
from extract_content import DocxParser
from telegram_bot import TelegramBot
from Bale_Bot import BaleBot
import os

async def send_to_telegram(content_with_images):
    print("Sending content and images to Telegram...")
    try:
        bot = TelegramBot()
        for section in content_with_images:
            await bot.send_message_with_images(section['text'], section['images'])
        print("All content and images sent successfully to Telegram!")
    except Exception as e:
        print(f"Error sending messages to Telegram: {e}")


async def send_to_bale(content_with_images):
    print("Sending content and images to Bale...")
    try:
        bale_bot = BaleBot()
        for section in content_with_images:
            text = section["text"]
            images = section.get("images", [])

            if images:
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
                    text = ""  # Avoid duplicate captions
            else:
                print(f"Sending text-only: {text}")
                await bale_bot.run(text)

        print("All content and images sent successfully to Bale!")
    except Exception as e:
        print(f"Error sending messages to Bale: {e}")


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

    # Ask the user where to send the content
    choice = input("Do you want to send the content to Telegram (T) or Bale (B)? ").strip().upper()

    destination = ""
    if choice == 'T':
        await send_to_telegram(content_with_images)
        destination = "t.me/mavazenews"
    elif choice == 'B':
        await send_to_bale(content_with_images)
        destination = "@mavazenews"
    else:
        print("Invalid choice. Please select 'T' for Telegram or 'B' for Bale.")
        return

    # Final success message
    print(f"\nMessages have been successfully sent to {destination}.\n")
    input("Press Enter to close the window...")  # Wait for user input to close

if __name__ == "__main__":
    asyncio.run(main())