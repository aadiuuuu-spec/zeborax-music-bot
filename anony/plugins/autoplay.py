# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from pyrogram import enums, filters, types

from anony import app, db, lang
from anony.helpers import buttons, can_manage_vc


_SMALL_CAPS = str.maketrans({
    "a": "ᴀ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ", "e": "ᴇ",
    "f": "ꜰ", "g": "ɢ", "h": "ʜ", "i": "ɪ", "j": "ᴊ",
    "k": "ᴋ", "l": "ʟ", "m": "ᴍ", "n": "ɴ", "o": "ᴏ",
    "p": "ᴘ", "q": "ǫ", "r": "ʀ", "s": "s", "t": "ᴛ",
    "u": "ᴜ", "v": "ᴠ", "w": "ᴡ", "x": "x", "y": "ʏ", "z": "ᴢ",
})


def _styled(text: str) -> str:
    # Some locale strings may contain escaped newline characters (\\n)
    # instead of real line breaks. Normalize them before sending to Telegram.
    return text.replace("\\\\n", "\n").replace("\\n", "\n").translate(_SMALL_CAPS)


@app.on_message(filters.command(["autoplay"]) & filters.group & ~app.bl_users)
@lang.language()
@can_manage_vc
async def _autoplay(_, m: types.Message):
    if len(m.command) == 1:
        enabled = await db.get_autoplay(m.chat.id)
        status = "ᴇɴᴀʙʟᴇᴅ" if enabled else "ᴅɪsᴀʙʟᴇᴅ"
        text = (
            "<blockquote>⚡ <b>ᴀᴜᴛᴏᴘʟᴀʏ sᴇᴛᴛɪɴɢs</b>\n\n"
            f"ᴄᴜʀʀᴇɴᴛ sᴛᴀᴛᴜs: <b>{status}</b>."
            "</blockquote>"
        )
        return await m.reply_text(
            text, reply_markup=buttons.autoplay_markup(m.chat.id)
        )

    value = m.command[1].lower()
    if value not in ["on", "off"]:
        return await m.reply_text(
            _styled(m.lang["autoplay_usage"]),
            reply_markup=buttons.autoplay_markup(m.chat.id),
        )

    enabled = value == "on"
    await db.set_autoplay(m.chat.id, enabled)
    key = "autoplay_on" if enabled else "autoplay_off"
    return await m.reply_text(
        _styled(m.lang[key]), reply_markup=buttons.autoplay_markup(m.chat.id)
    )
