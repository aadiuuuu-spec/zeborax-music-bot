# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from pyrogram import enums, types

from anony import app, config, lang
from anony.core.lang import lang_codes


class Inline:
    def __init__(self):
        self.ikm = types.InlineKeyboardMarkup
        self.ikb = types.InlineKeyboardButton

    def cancel_dl(self, text) -> types.InlineKeyboardMarkup:
        return self.ikm([[self.ikb(text=text, callback_data="cancel_dl")]])

    def controls(
        self,
        chat_id: int,
        status: str = None,
        timer: str = None,
        remove: bool = False,
    ) -> types.InlineKeyboardMarkup:
        keyboard = []
        if status:
            keyboard.append(
                [self.ikb(text=status, callback_data=f"controls status {chat_id}")]
            )
        elif timer:
            keyboard.append(
                [self.ikb(text=timer, callback_data=f"controls status {chat_id}")]
            )

        if not remove:
            keyboard.append(
                [
                    self.ikb(text="▷", callback_data=f"controls resume {chat_id}", style=enums.ButtonStyle.PRIMARY),
                    self.ikb(text="II", callback_data=f"controls pause {chat_id}", style=enums.ButtonStyle.SUCCESS),
                    self.ikb(text="⥁", callback_data=f"controls replay {chat_id}", style=enums.ButtonStyle.PRIMARY),
                    self.ikb(text="‣‣I", callback_data=f"controls skip {chat_id}", style=enums.ButtonStyle.SUCCESS),
                    self.ikb(text="▢", callback_data=f"controls stop {chat_id}", style=enums.ButtonStyle.PRIMARY),
                ]
            )
            keyboard.append(
                [self.ikb(text="𝖢ᴏᴍᴍᴀɴᴅs", callback_data="help", style=enums.ButtonStyle.SUCCESS)]
            )
        return self.ikm(keyboard)

    def help_markup(
        self, _lang: dict, back: bool = False
    ) -> types.InlineKeyboardMarkup:
        if back:
            rows = [
                [
                    self.ikb(text="𝖡ᴀᴄᴋ", callback_data="help back", style=enums.ButtonStyle.PRIMARY),
                    self.ikb(text="𝖢ʟᴏsᴇ", callback_data="help close", style=enums.ButtonStyle.SUCCESS),
                ]
            ]
        else:
            labels = [
                "𝖠ᴅᴍɪɴs",
                "𝖠ᴜᴛʜ",
                "𝖡ʟᴀᴄᴋʟɪsᴛ",
                "𝖫ᴀɴɢᴜᴀɢᴇ",
                "𝖯ɪɴɢ",
                "𝖯ʟᴀʏ",
                "𝖰ᴜᴇᴜᴇ",
                "𝖲ᴛᴀᴛs",
                "𝖲ᴜᴅᴏᴇʀs",
            ]
            cbs = ["admins", "auth", "blist", "lang", "ping", "play", "queue", "stats", "sudo"]
            styles = [enums.ButtonStyle.PRIMARY, enums.ButtonStyle.SUCCESS]
            buttons = [
                self.ikb(
                    text=label,
                    callback_data=f"help {cb}",
                    style=styles[i % 2],
                )
                for i, (label, cb) in enumerate(zip(labels, cbs))
            ]
            rows = [buttons[i : i + 3] for i in range(0, len(buttons), 3)]

        return self.ikm(rows)

    def lang_markup(self, _lang: str) -> types.InlineKeyboardMarkup:
        langs = lang.get_languages()

        buttons = [
            self.ikb(
                text=f"{name} ({code}) {'✔️' if code == _lang else ''}",
                callback_data=f"lang_change {code}",
            )
            for code, name in langs.items()
        ]
        rows = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
        return self.ikm(rows)

    def ping_markup(self, text: str) -> types.InlineKeyboardMarkup:
        return self.ikm([[self.ikb(text=text, url=config.SUPPORT_CHAT)]])

    def play_queued(
        self, chat_id: int, item_id: str, _text: str
    ) -> types.InlineKeyboardMarkup:
        return self.ikm(
            [
                [
                    self.ikb(
                        text=_text, callback_data=f"controls force {chat_id} {item_id}",
                        style=enums.ButtonStyle.DANGER,
                    )
                ]
            ]
        )

    def autoplay_markup(self, chat_id: int) -> types.InlineKeyboardMarkup:
        return self.ikm(
            [[
                self.ikb(
                    text="ENABLE",
                    callback_data=f"autoplay enable {chat_id}",
                    style=enums.ButtonStyle.PRIMARY,
                ),
                self.ikb(
                    text="DISABLE",
                    callback_data=f"autoplay disable {chat_id}",
                    style=enums.ButtonStyle.DANGER,
                ),
            ]]
        )

    def queue_markup(
        self, chat_id: int, _text: str, playing: bool
    ) -> types.InlineKeyboardMarkup:
        _action = "pause" if playing else "resume"
        return self.ikm(
            [[self.ikb(text=_text, callback_data=f"controls {_action} {chat_id} q")]]
        )

    def settings_markup(
        self, lang: dict, admin_only: bool, cmd_delete: bool, language: str, chat_id: int
    ) -> types.InlineKeyboardMarkup:
        return self.ikm(
            [
                [
                    self.ikb(
                        text=lang["play_mode"] + " ➜",
                        callback_data="settings",
                    ),
                    self.ikb(text=admin_only, callback_data="settings play"),
                ],
                [
                    self.ikb(
                        text=lang["cmd_delete"] + " ➜",
                        callback_data="settings",
                    ),
                    self.ikb(text=cmd_delete, callback_data="settings delete"),
                ],
                [
                    self.ikb(
                        text=lang["language"] + " ➜",
                        callback_data="settings",
                    ),
                    self.ikb(text=lang_codes[language], callback_data="language"),
                ],
            ]
        )

    def start_key(
        self, lang: dict, private: bool = False
    ) -> types.InlineKeyboardMarkup:
        rows = [
            [
                self.ikb(
                    text="𝖠ᴅᴅ ᴍᴇ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ",
                    url=f"https://t.me/{app.username}?startgroup=true",
                    style=enums.ButtonStyle.PRIMARY,
                )
            ],
            [
                self.ikb(text="𝖢ᴏᴍᴍᴀɴᴅs", callback_data="help", style=enums.ButtonStyle.SUCCESS),
                self.ikb(text="𝖫ᴀɴɢᴜᴀɢᴇ", callback_data="language", style=enums.ButtonStyle.PRIMARY),
            ],
            [
                self.ikb(text="𝖲ᴜᴘᴘᴏʀᴛ", url=config.SUPPORT_CHAT, style=enums.ButtonStyle.SUCCESS),
                self.ikb(text="𝖣ᴇᴠᴇʟᴏᴘᴇʀ", url="https://t.me/II_YUTA_II", style=enums.ButtonStyle.PRIMARY),
            ],
        ]
        return self.ikm(rows)

    def yt_key(self, link: str) -> types.InlineKeyboardMarkup:
        return self.ikm(
            [
                [
                    self.ikb(text="❐", copy_text=link),
                    self.ikb(text="Youtube", url=link),
                ],
            ]
        )
