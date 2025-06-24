import os
import aiohttp
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, ReplyKeyboardRemove

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

stop_requested = False

@app.on_message(filters.command("stop") & filters.private)
async def stop_command(client: Client, message: Message):
    global stop_requested
    stop_requested = True
    await message.reply("⏹️ Stopping the current operation.", reply_markup=ReplyKeyboardRemove())

@app.on_message(filters.document & filters.private)
async def handle_txt_file(client: Client, message: Message):
    global stop_requested
    stop_requested = False  # Reset stop flag at the start

    if not message.document.file_name.endswith(".txt"):
        await message.reply("Please send a .txt file containing PDF URLs.")
        return

    txt_path = os.path.join(DOWNLOAD_DIR, message.document.file_name)
    await message.download(txt_path)

    entries = []
    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if ":" in line:
                parts = line.rsplit(":", 1)
                if len(parts) == 2:
                    caption, url = parts
                    caption = caption.strip()
                    url = url.strip()
                    entries.append((caption, url))
            else:
                url = line
                entries.append(("", url))

    await message.reply(f"Found {len(entries)} URLs. Starting download and upload...")

    for caption, url in entries:
        if stop_requested:
            await message.reply("⏹️ Operation stopped by user.")
            break
        pdf_name = url.split("/")[-1].split("?")[0]
        if not pdf_name.lower().endswith(".pdf"):
            pdf_name += ".pdf"
        pdf_path = os.path.join(DOWNLOAD_DIR, pdf_name)
        await message.reply(f"Downloading: {caption or pdf_name}")
        success = await download_pdf(url, pdf_path)
        if success:
            await client.send_document(CHANNEL_ID, pdf_path, caption=caption or pdf_name)
            await message.reply(f"Uploaded: {caption or pdf_name}")
            os.remove(pdf_path)
        else:
            await message.reply(f"Failed to download: {url}")

    os.remove(txt_path)
    if not stop_requested:
        await message.reply("✅ All done!")
    else:
        await message.reply("Stopped before completing all files.")

if __name__ == "__main__":
    app.run()
