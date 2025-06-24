import os
import aiohttp
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, ReplyKeyboardRemove

# Configs - replace with your actual values or use environment variables
API_ID = int(os.environ.get("API_ID", 23644766))
API_HASH = os.environ.get("API_HASH", "9dc15dd41be1a26016b2ebac611868f5")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "6159513044:AAHJgOjXo8EsdYRiGZWXkllOYLl5GNlS_us")
CHANNEL_ID = os.environ.get("CHANNEL_ID", "@sdfghjxcvbasdf")  # or -100xxxxxxxxxx

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

app = Client("pdf_downloader_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

stop_requested = False


async def download_pdf(url, dest_path, retries=3):
    for attempt in range(retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                    if resp.status == 200:
                        with open(dest_path, "wb") as f:
                            async for chunk in resp.content.iter_chunked(2048):
                                f.write(chunk)
                        return True
                    else:
                        print(f"Attempt {attempt+1}: Failed with status {resp.status}")
        except Exception as e:
            print(f"Attempt {attempt+1}: Error downloading {url}: {e}")
        await asyncio.sleep(2)  # Wait before retry
    return False


@app.on_message(filters.command("stop") & filters.private)
async def stop_command(client: Client, message: Message):
    global stop_requested
    stop_requested = True
    await message.reply("⏹️ Stopping the current operation.", reply_markup=ReplyKeyboardRemove())


@app.on_message(filters.document & filters.private)
async def handle_txt_file(client: Client, message: Message):
    global stop_requested
    stop_requested = False

    doc = message.document
    if not doc.file_name.endswith(".txt"):
        return await message.reply("Please send a `.txt` file containing PDF URLs.")

    txt_path = os.path.join(DOWNLOAD_DIR, doc.file_name)
    await message.download(txt_path)

    entries = []
    with open(txt_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            idx = line.find("https://")
            if idx != -1:
                caption = line[:idx].strip(" :")
                url = line[idx:].strip()
                entries.append((caption, url))
            else:
                entries.append(("", line.strip()))

    await message.reply(f"📄 Found {len(entries)} URLs. Starting downloads...")

    for caption, url in entries:
        if stop_requested:
            await message.reply("⏹️ Operation stopped.")
            break

        if url.startswith("//"):
            url = "https:" + url

        file_name = url.split("/")[-1].split("?")[0]
        if not file_name.lower().endswith(".pdf"):
            file_name += ".pdf"

        pdf_path = os.path.join(DOWNLOAD_DIR, file_name)

        await message.reply(f"⬇️ Downloading: {caption or file_name}")
        success = await download_pdf(url, pdf_path)

        if success:
            try:
                await client.send_document(
                    CHANNEL_ID,
                    document=pdf_path,
                    caption=caption or file_name
                )
                await message.reply(f"✅ Uploaded: {caption or file_name}")
            except Exception as e:
                await message.reply(f"❌ Upload failed: {file_name}\nError: {e}")
            finally:
                os.remove(pdf_path)
        else:
            await message.reply(f"❌ Download failed: {url}")

    os.remove(txt_path)
    if not stop_requested:
        await message.reply("✅ All tasks completed!")
    else:
        await message.reply("⏹️ Stopped before completing all downloads.")


if __name__ == "__main__":
    app.run()
