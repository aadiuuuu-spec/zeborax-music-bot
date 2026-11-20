import asyncio
import logging
import os
import random
from collections import defaultdict, deque
from pathlib import Path

import pyrogram.errors

# Compatibility aliases: PyTgCalls imports the older spelling.
if not hasattr(pyrogram.errors, "GroupcallForbidden"):
    pyrogram.errors.GroupcallForbidden = getattr(
        pyrogram.errors, "GroupCallForbidden", Exception
    )
if not hasattr(pyrogram.errors, "GroupcallInvalid"):
    pyrogram.errors.GroupcallInvalid = getattr(
        pyrogram.errors, "GroupCallInvalid", Exception
    )

from pyrogram import Client, filters
from pyrogram.types import Message
from pytgcalls import PyTgCalls, filters as call_filters
from pytgcalls.types import MediaStream, StreamEnded

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("zeborax")

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
SESSION_STRING = os.environ["SESSION_STRING"]
OWNER_USERNAME = os.getenv("OWNER_USERNAME", "II_YUTA_II")

Path("downloads").mkdir(exist_ok=True)

bot = Client(
    "zeborax-bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)
assistant = Client(
    "zeborax-assistant",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING,
)
calls = PyTgCalls(assistant)

queues = defaultdict(deque)
current = {}
loop_mode = defaultdict(lambda: "off")  # off, track, queue
autoplay = defaultdict(bool)
volume = defaultdict(lambda: 100)
locks = defaultdict(asyncio.Lock)


def track_title(message: Message) -> str:
    media = message.audio or message.document or message.voice
    return getattr(media, "file_name", None) or getattr(media, "title", None) or "Telegram audio"


async def download_audio(message: Message) -> dict | None:
    media = message.audio or message.document or message.voice
    if not media:
        return None
    if getattr(media, "mime_type", "").startswith("video/"):
        return None
    # Telegram Bot API download limit is 20 MB.
    if getattr(media, "file_size", 0) > 20 * 1024 * 1024:
        return None
    file_path = await bot.download_media(message, file_name="downloads/")
    if not file_path:
        return None
    return {"path": file_path, "title": track_title(message)}


async def play_next(chat_id: int):
    async with locks[chat_id]:
        q = queues[chat_id]
        if q:
            track = q.popleft()
        elif autoplay[chat_id] and current.get(chat_id):
            track = current[chat_id]
        else:
            current.pop(chat_id, None)
            try:
                await calls.leave_call(chat_id)
            except Exception:
                pass
            return
        try:
            await calls.play(
                chat_id,
                MediaStream(track["path"], video_flags=MediaStream.Flags.IGNORE),
            )
            current[chat_id] = track
        except Exception:
            log.exception("Could not start playback in %s", chat_id)
            current.pop(chat_id, None)


@calls.on_update(call_filters.stream_end())
async def on_stream_end(_, update: StreamEnded):
    chat_id = update.chat_id
    if loop_mode[chat_id] == "track" and current.get(chat_id):
        queues[chat_id].appendleft(current[chat_id])
    elif loop_mode[chat_id] == "queue" and current.get(chat_id):
        queues[chat_id].append(current[chat_id])
    await play_next(chat_id)


@bot.on_message(filters.group & (filters.audio | filters.voice | filters.document))
async def incoming_audio(_, message: Message):
    track = await download_audio(message)
    if not track:
        await message.reply_text("Audio file nahi mila, ya file 20 MB se badi hai. Chhoti audio file bhejo.")
        return
    chat_id = message.chat.id
    queues[chat_id].append(track)
    if not current.get(chat_id):
        await play_next(chat_id)
        await message.reply_text(f"Queue mein add kiya: **{track['title']}**")
    else:
        await message.reply_text(f"Queue mein add kiya: **{track['title']}**")


@bot.on_message(filters.group & filters.command("start"))
async def start_cmd(_, message: Message):
    await message.reply_text(
        "**ZeboraX Music Bot**\n"
        "Group voice chat mein audio play karne ke liye audio file bhejo.\n"
        "Commands ke liye /help use karo."
    )


@bot.on_message(filters.group & filters.command("help"))
async def help_cmd(_, message: Message):
    await message.reply_text(
        "**ZeboraX Music Bot Commands**\n"
        "/play — replied audio ko queue mein add karo\n"
        "/pause — playback pause\n"
        "/resume — playback resume\n"
        "/skip — next track\n"
        "/queue — queue dekho\n"
        "/shuffle — queue shuffle\n"
        "/loop — loop off/track/queue\n"
        "/autoplay — last track repeat toggle\n"
        "/volume 1-200 — volume set\n"
        "/stop — playback stop\n"
        "/end — stop karke voice chat se leave\n\n"
        "Audio file ko group mein bhejne se bhi queue mein add ho jayega."
    )


@bot.on_message(filters.group & filters.command("play"))
async def play_cmd(_, message: Message):
    if not message.reply_to_message:
        await message.reply_text("Kisi audio file par reply karke /play bhejo, ya audio seedha group mein bhejo.")
        return
    track = await download_audio(message.reply_to_message)
    if not track:
        await message.reply_text("Valid audio file nahi mili (maximum 20 MB).")
        return
    chat_id = message.chat.id
    queues[chat_id].append(track)
    if not current.get(chat_id):
        await play_next(chat_id)
    await message.reply_text(f"Queue mein add kiya: **{track['title']}**")


@bot.on_message(filters.group & filters.command("pause"))
async def pause_cmd(_, message: Message):
    try:
        await calls.pause(message.chat.id)
        await message.reply_text("⏸️ Paused.")
    except Exception:
        await message.reply_text("Abhi kuch play nahi ho raha.")


@bot.on_message(filters.group & filters.command("resume"))
async def resume_cmd(_, message: Message):
    try:
        await calls.resume(message.chat.id)
        await message.reply_text("▶️ Resumed.")
    except Exception:
        await message.reply_text("Resume nahi ho paya. Voice chat active hai?")


@bot.on_message(filters.group & filters.command("skip"))
async def skip_cmd(_, message: Message):
    chat_id = message.chat.id
    if not current.get(chat_id):
        await message.reply_text("Abhi kuch play nahi ho raha.")
        return
    try:
        await calls.leave_call(chat_id)
    except Exception:
        pass
    current.pop(chat_id, None)
    await play_next(chat_id)
    await message.reply_text("⏭️ Skipped.")


@bot.on_message(filters.group & filters.command("queue"))
async def queue_cmd(_, message: Message):
    q = list(queues[message.chat.id])
    if not q and not current.get(message.chat.id):
        await message.reply_text("Queue khaali hai.")
        return
    lines = []
    if current.get(message.chat.id):
        lines.append(f"Now: {current[message.chat.id]['title']}")
    lines.extend(f"{i}. {item['title']}" for i, item in enumerate(q, 1))
    await message.reply_text("\n".join(lines)[:4000])


@bot.on_message(filters.group & filters.command("shuffle"))
async def shuffle_cmd(_, message: Message):
    random.shuffle(queues[message.chat.id])
    await message.reply_text("🔀 Queue shuffle kar di.")


@bot.on_message(filters.group & filters.command("loop"))
async def loop_cmd(_, message: Message):
    chat_id = message.chat.id
    modes = ["off", "track", "queue"]
    loop_mode[chat_id] = modes[(modes.index(loop_mode[chat_id]) + 1) % len(modes)]
    await message.reply_text(f"Loop: **{loop_mode[chat_id]}**")


@bot.on_message(filters.group & filters.command("autoplay"))
async def autoplay_cmd(_, message: Message):
    chat_id = message.chat.id
    autoplay[chat_id] = not autoplay[chat_id]
    await message.reply_text(f"Autoplay: **{'ON' if autoplay[chat_id] else 'OFF'}** (queue khaali hone par current audio repeat hoga).")


@bot.on_message(filters.group & filters.command("volume"))
async def volume_cmd(_, message: Message):
    args = message.command
    if len(args) < 2 or not args[1].isdigit() or not 1 <= int(args[1]) <= 200:
        await message.reply_text("Use: /volume 1-200")
        return
    chat_id = message.chat.id
    volume[chat_id] = int(args[1])
    try:
        await calls.change_volume_call(chat_id, volume[chat_id])
        await message.reply_text(f"Volume set: {volume[chat_id]}%")
    except Exception:
        await message.reply_text("Volume change nahi hua. Pehle audio play karo.")


@bot.on_message(filters.group & filters.command(["stop", "end"]))
async def stop_cmd(_, message: Message):
    chat_id = message.chat.id
    queues[chat_id].clear()
    current.pop(chat_id, None)
    autoplay[chat_id] = False
    try:
        calls.leave_call(chat_id)
    except Exception:
        pass
    await message.reply_text("⏹️ Playback stopped. Voice chat se leave kar diya.")


async def main():
    await bot.start()
    await assistant.start()
    await calls.start()
    me = await bot.get_me()
    log.info("Started as @%s", me.username)
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
