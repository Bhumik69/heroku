import os
import aiohttp
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message

API_ID = int(os.environ.get("API_ID", 23644766))  # Set in Heroku config vars
API_HASH = os.environ.get("API_HASH", "9dc15dd41be1a26016b2ebac611868f5")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "6159513044:AAHJgOjXo8EsdYRiGZWXkllOYLl5GNlS_us")
CHANNEL_ID = os.environ.get("CHANNEL_ID", "@sdfghjxcvbasdf")  # or -100xxxxxxxxxx

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

app = Client("pdf_downloader_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

async def download_pdf(url, dest):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    with open(dest, "wb") as f:
                        while True:
                            chunk = await resp.content.read(1024)
                            if not chunk:
                                break
                            f.write(chunk)
                    return True
    except Exception as e:
        print(f"Download failed for {url}: {e}")
    return False

@app.on_message(filters.document & filters.private)
async def handle_txt_file(client: Client, message: Message):
    if not message.document.file_name.endswith(".txt"):
        await message.reply("Please send a .txt file containing PDF URLs.")
        return

    txt_path = os.path.join(DOWNLOAD_DIR, message.document.file_name)
    await message.download(txt_path)

    with open(txt_path, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

    await message.reply(f"Found {len(urls)} URLs. Starting download and upload...")

    for url in urls:
        pdf_name = url.split("/")[-1].split("?")[0]
        if not pdf_name.lower().endswith(".pdf"):
            pdf_name += ".pdf"
        pdf_path = os.path.join(DOWNLOAD_DIR, pdf_name)
        await message.reply(f"Downloading: {pdf_name}")
        success = await download_pdf(url, pdf_path)
        if success:
            await client.send_document(CHANNEL_ID, pdf_path, caption=pdf_name)
            await message.reply(f"Uploaded: {pdf_name}")
            os.remove(pdf_path)
        else:
            await message.reply(f"Failed to download: {url}")

    os.remove(txt_path)
    await message.reply("✅ All done!")

if __name__ == "__main__":
    app.run()