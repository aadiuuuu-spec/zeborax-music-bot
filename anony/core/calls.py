# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from html import escape, unescape
import re

from ntgcalls import (ConnectionNotFound, TelegramServerError,
                      RTMPStreamingUnsupported, ConnectionError,
                      TransportParseException)
from pyrogram.errors import (ChatSendMediaForbidden, ChatSendPhotosForbidden,
                             MessageIdInvalid)
from pyrogram.types import InputMediaPhoto, Message
from pytgcalls import PyTgCalls, exceptions, types
from pytgcalls.pytgcalls_session import PyTgCallsSession

from anony import (app, config, db, lang, logger,
                   queue, thumb, userbot, yt)
from anony.helpers import Media, Track, buttons

_SMALL_CAPS = str.maketrans({
    "a": "ᴀ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ", "e": "ᴇ",
    "f": "ꜰ", "g": "ɢ", "h": "ʜ", "i": "ɪ", "j": "ᴊ",
    "k": "ᴋ", "l": "ʟ", "m": "ᴍ", "n": "ɴ", "o": "ᴏ",
    "p": "ᴘ", "q": "ǫ", "r": "ʀ", "s": "s", "t": "ᴛ",
    "u": "ᴜ", "v": "ᴠ", "w": "ᴡ", "x": "x", "y": "ʏ", "z": "ᴢ",
})


def style_error(text: str) -> str:
    """Apply the bot's small-caps style without changing HTML tags or URLs."""
    return re.sub(
        r"(<[^>]+>)|([^<]+)",
        lambda match: match.group(1) or match.group(2).translate(_SMALL_CAPS),
        text,
    )


class TgCall(PyTgCalls):
    def __init__(self):
        self.clients = []

    async def pause(self, chat_id: int) -> bool:
        client = await db.get_assistant(chat_id)
        await db.playing(chat_id, paused=True)
        try:
            return await client.pause(chat_id)
        except (ConnectionNotFound, exceptions.NotInCallError):
            await self.stop(chat_id)

    async def resume(self, chat_id: int) -> bool:
        client = await db.get_assistant(chat_id)
        await db.playing(chat_id, paused=False)
        try:
            return await client.resume(chat_id)
        except (ConnectionNotFound, exceptions.NotInCallError):
            await self.stop(chat_id)

    async def stop(self, chat_id: int) -> None:
        client = await db.get_assistant(chat_id)
        queue.clear(chat_id)
        await db.remove_call(chat_id)
        await db.set_loop(chat_id, 0)

        try:
            await client.leave_call(chat_id, close=False)
        except Exception:
            pass


    async def play_media(
        self,
        chat_id: int,
        message: Message,
        media: Media | Track,
        seek_time: int = 0,
    ) -> None:
        client = await db.get_assistant(chat_id)
        _lang = await lang.get_lang(chat_id)
        _thumb = (
            await thumb.generate(media)
            if isinstance(media, Track)
            else config.DEFAULT_THUMB
        ) if config.THUMB_GEN else None

        if not media.file_path:
            await message.edit_text(style_error(_lang["error_no_file"].format(config.SUPPORT_CHAT)))
            return await self.play_next(chat_id)

        stream = types.MediaStream(
            media_path=media.file_path,
            audio_parameters=types.AudioQuality.HIGH,
            video_parameters=types.VideoQuality.HD_720p,
            audio_flags=types.MediaStream.Flags.REQUIRED,
            video_flags=(
                types.MediaStream.Flags.AUTO_DETECT
                if media.video
                else types.MediaStream.Flags.IGNORE
            ),
            ffmpeg_parameters=f"-ss {seek_time}" if seek_time > 1 else None,
        )
        try:
            await client.play(
                chat_id=chat_id,
                stream=stream,
                config=types.GroupCallConfig(auto_start=False),
            )
            if not seek_time:
                media.time = 1
                await db.add_call(chat_id)
                raw_title = str(media.title or "Unknown")
                short_title = raw_title.split("|", 1)[0].split("(", 1)[0].strip() or raw_title
                title = escape(short_title)
                url = escape(str(media.url or ""), quote=True)
                raw_user = str(media.user or "Unknown")
                raw_user = unescape(re.sub(r"<[^>]*>", "", raw_user)).strip()
                played_by = escape(raw_user or "Unknown")
                text = (
                    "<blockquote>➻ Sᴛᴀʀᴛᴇᴅ Sᴛʀᴇᴀᴍɪɴɢ\n"
                    f"🎧 Sᴏᴜɴᴅ Ɛɴɢᴀɢᴇᴅ ┊ {escape(str(media.duration or '0:00'))} ◤"
                    "</blockquote>\n\n"
                    "<blockquote>"
                    f'🎶 𝖳ɪᴛʟᴇ : <a href="{url}">{title}</a>\n'
                    f"✨ 𝖯ʟᴀʏᴇᴅ 𝖡ʏ : {played_by}"
                    "</blockquote>"
                )
                keyboard = buttons.controls(chat_id)
                try:
                    if _thumb:
                        await message.edit_media(
                            media=InputMediaPhoto(
                                media=_thumb,
                                caption=text,
                                has_spoiler=True,
                            ),
                            reply_markup=keyboard,
                        )
                    else:
                        await message.edit_text(text, reply_markup=keyboard)
                except (ChatSendMediaForbidden, ChatSendPhotosForbidden, MessageIdInvalid):
                    if _thumb:
                        sent = await app.send_photo(
                            chat_id=chat_id,
                            photo=_thumb,
                            caption=text,
                            has_spoiler=True,
                            reply_markup=keyboard,
                        )
                    else:
                        sent = await app.send_message(
                            chat_id=chat_id,
                            text=text,
                            reply_markup=keyboard,
                        )
                    media.message_id = sent.id
        except FileNotFoundError:
            await message.edit_text(style_error(_lang["error_no_file"].format(config.SUPPORT_CHAT)))
            await self.play_next(chat_id)
        except exceptions.NoActiveGroupCall:
            await self.stop(chat_id)
            await message.edit_text(style_error(_lang["error_no_call"]))
        except exceptions.NoAudioSourceFound:
            await message.edit_text(style_error(_lang["error_no_audio"]))
            await self.play_next(chat_id)
        except (ConnectionError, ConnectionNotFound, TelegramServerError,
                TransportParseException, TimeoutError):
            await self.stop(chat_id)
            await message.edit_text(style_error(_lang["error_tg_server"]))
        except RTMPStreamingUnsupported:
            await self.stop(chat_id)
            await message.edit_text(style_error(_lang["error_rtmp"]))


    async def replay(self, chat_id: int) -> None:
        if not await db.get_call(chat_id):
            return

        media = queue.get_current(chat_id)
        _lang = await lang.get_lang(chat_id)
        msg = await app.send_message(chat_id=chat_id, text=_lang["play_again"])
        media.message_id = msg.id
        await self.play_media(chat_id, msg, media)


    async def play_next(self, chat_id: int) -> None:
        if loop := await db.get_loop(chat_id):
            await db.set_loop(chat_id, loop - 1)
            return await self.replay(chat_id)

        previous = queue.get_current(chat_id)
        if previous:
            queue.remember_played(chat_id, previous.id)
        media = queue.get_next(chat_id)

        # Always play user-requested queue items first. Generate an autoplay
        # recommendation only when the user queue is empty.
        if previous and media is None and await db.get_autoplay(chat_id):
            title = str(previous.title or "").strip()
            queued_ids = {item.id for item in queue.get_queue(chat_id)}
            excluded_ids = queued_ids | queue.recent_ids(chat_id) | {previous.id}
            related = (
                await yt.search_related(
                    title,
                    channel=getattr(previous, "channel_name", None) or "",
                    exclude_ids=excluded_ids,
                    video=previous.video,
                    max_duration=config.DURATION_LIMIT,
                    current_id=previous.id,
                )
                if title else None
            )
            if related:
                related.user = "AutoPlay"
                queue.add(chat_id, related)
                logger.info(
                    f"Autoplay selected related track {related.title!r} "
                    f"({related.id}) for chat {chat_id}"
                )
                if media is None:
                    media = related
            else:
                logger.warning(
                    f"Autoplay found no eligible related track for "
                    f"{title!r} in chat {chat_id}"
                )

        # The queue can be empty when autoplay is disabled or when no
        # related track is found. Check before reading media.message_id.
        if media is None:
            return await self.stop(chat_id)

        try:
            if media.message_id:
                await app.delete_messages(
                    chat_id=chat_id,
                    message_ids=media.message_id,
                    revoke=True,
                )
                media.message_id = 0
        except Exception:
            pass

        _lang = await lang.get_lang(chat_id)
        msg = await app.send_message(chat_id=chat_id, text=_lang["play_next"])
        if not media.file_path:
            media.file_path = await yt.download(media.id, video=media.video)
            if not media.file_path:
                await self.play_next(chat_id)
                return await msg.edit_text(
                    style_error(_lang["error_no_file"].format(config.SUPPORT_CHAT))
                )

        media.message_id = msg.id
        await self.play_media(chat_id, msg, media)


    async def ping(self) -> float:
        pings = [client.ping for client in self.clients]
        return round(sum(pings) / len(pings), 2)


    async def decorators(self, client: PyTgCalls) -> None:
        @client.on_update()
        async def update_handler(_, update: types.Update) -> None:
            if isinstance(update, types.StreamEnded):
                if update.stream_type == types.StreamEnded.Type.AUDIO:
                    await self.play_next(update.chat_id)
            elif isinstance(update, types.ChatUpdate):
                if update.status in [
                    types.ChatUpdate.Status.KICKED,
                    types.ChatUpdate.Status.LEFT_GROUP,
                    types.ChatUpdate.Status.CLOSED_VOICE_CHAT,
                ]:
                    await self.stop(update.chat_id)


    async def boot(self) -> None:
        PyTgCallsSession.notice_displayed = True
        for ub in userbot.clients:
            client = PyTgCalls(ub)
            await client.start()
            self.clients.append(client)
            await self.decorators(client)
        logger.info("PyTgCalls client(s) started.")
