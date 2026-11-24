# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import pyrogram

from anony import config, logger


class Bot(pyrogram.Client):
    def __init__(self):
        super().__init__(
            name="anony",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            parse_mode=pyrogram.enums.ParseMode.HTML,
            max_concurrent_transmissions=7,
            link_preview_options=pyrogram.types.LinkPreviewOptions(is_disabled=True),
        )
        self.owner = config.OWNER_ID
        self.logger = config.LOGGER_ID
        self.bl_users = pyrogram.filters.user()
        self.sudoers = pyrogram.filters.user(self.owner)

    async def _register_command_menu(self):
        """Register public commands with the original small-caps style."""
        public_commands = [
            ("start", "Sᴛᴀʀᴛ ᴛʜᴇ ᴍᴜsɪᴄ ʙᴏᴛ"),
            ("help", "Sʜᴏᴡ ʜᴇʟᴘ ᴀɴᴅ ᴄᴏᴍᴍᴀɴᴅ ᴄᴀᴛᴇɢᴏʀɪᴇs"),
            ("play", "Pʟᴀʏ ᴀ sᴏɴɢ ᴏʀ ᴀᴜᴅɪᴏ ʟɪɴᴋ"),
            ("vplay", "Pʟᴀʏ ᴀ ᴠɪᴅᴇᴏ ɪɴ ᴛʜᴇ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ"),
            ("pause", "Pᴀᴜsᴇ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛ sᴛʀᴇᴀᴍ"),
            ("resume", "Rᴇsᴜᴍᴇ ᴛʜᴇ ᴘᴀᴜsᴇᴅ sᴛʀᴇᴀᴍ"),
            ("skip", "Sᴋɪᴘ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛ ᴛʀᴀᴄᴋ"),
            ("stop", "Sᴛᴏᴘ ᴘʟᴀʏʙᴀᴄᴋ ᴀɴᴅ ᴄʟᴇᴀʀ ᴛʜᴇ ǫᴜᴇᴜᴇ"),
            ("queue", "Sʜᴏᴡ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛ ᴍᴜsɪᴄ ǫᴜᴇᴜᴇ"),
            ("loop", "Sᴇᴛ ᴏʀ ᴅɪsᴀʙʟᴇ ᴛʀᴀᴄᴋ ʟᴏᴏᴘɪɴɢ"),
            ("seek", "Sᴇᴇᴋ ꜰᴏʀᴡᴀʀᴅ ɪɴ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛ ᴛʀᴀᴄᴋ"),
            ("seekback", "Sᴇᴇᴋ ʙᴀᴄᴋᴡᴀʀᴅ ɪɴ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛ ᴛʀᴀᴄᴋ"),
            ("autoplay", "Eɴᴀʙʟᴇ, ᴅɪsᴀʙʟᴇ, ᴏʀ ᴄʜᴇᴄᴋ ᴀᴜᴛᴏᴘʟᴀʏ"),
            ("ping", "Cʜᴇᴄᴋ ʙᴏᴛ ʀᴇsᴘᴏɴsᴇ ᴀɴᴅ sʏsᴛᴇᴍ sᴛᴀᴛᴜs"),
            ("stats", "Sʜᴏᴡ ʙᴏᴛ sᴛᴀᴛɪsᴛɪᴄs"),
            ("lang", "Cʜᴀɴɢᴇ ᴛʜᴇ ᴄʜᴀᴛ ʟᴀɴɢᴜᴀɢᴇ"),
        ]
        owner_commands = [
            ("auth", "Aᴜᴛʜᴏʀɪᴢᴇ ᴀ ᴜsᴇʀ ᴛᴏ ᴄᴏɴᴛʀᴏʟ ᴘʟᴀʏʙᴀᴄᴋ"),
            ("unauth", "Rᴇᴍᴏᴠᴇ ᴀ ᴘʟᴀʏʙᴀᴄᴋ-ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴜsᴇʀ"),
            ("blacklist", "Bʟᴀᴄᴋʟɪsᴛ ᴀ ᴄʜᴀᴛ ᴏʀ ᴜsᴇʀ"),
            ("unblacklist", "Rᴇᴍᴏᴠᴇ ᴀ ᴄʜᴀᴛ ᴏʀ ᴜsᴇʀ ꜰʀᴏᴍ ʙʟᴀᴄᴋʟɪsᴛ"),
            ("sudoers", "Sʜᴏᴡ ᴛʜᴇ sᴜᴅᴏ ᴜsᴇʀ ʟɪsᴛ"),
            ("ac", "Sʜᴏᴡ ᴛʜᴇ ᴀᴄᴛɪᴠᴇ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ᴄᴏᴜɴᴛ"),
            ("activevc", "Lɪsᴛ ᴀᴄᴛɪᴠᴇ ᴠᴏɪᴄᴇ ᴄʜᴀᴛs"),
            ("broadcast", "Bʀᴏᴀᴅᴄᴀsᴛ ᴀ ʀᴇᴘʟɪᴇᴅ ᴍᴇssᴀɢᴇ"),
            ("eval", "Exᴇᴄᴜᴛᴇ ᴀɴ ᴏᴡɴᴇʀ ᴄᴏᴅᴇ sɴɪᴘᴘᴇᴛ"),
            ("logs", "Gᴇᴛ ᴛʜᴇ ʟᴀᴛᴇsᴛ ʙᴏᴛ ʟᴏɢ ꜰɪʟᴇ"),
            ("logger", "Eɴᴀʙʟᴇ ᴏʀ ᴅɪsᴀʙʟᴇ ʙᴏᴛ ʟᴏɢɢɪɴɢ"),
            ("restart", "Rᴇsᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ"),
            ("addsudo", "Aᴅᴅ ᴀ sᴜᴅᴏ ᴜsᴇʀ"),
            ("rmsudo", "Rᴇᴍᴏᴠᴇ ᴀ sᴜᴅᴏ ᴜsᴇʀ"),
        ]

        make_commands = lambda items: [
            pyrogram.types.BotCommand(command, description)
            for command, description in items
        ]

        try:
            await self.set_bot_commands(
                make_commands(public_commands),
                scope=pyrogram.types.BotCommandScopeDefault(),
            )
            await self.set_bot_commands(
                make_commands(public_commands),
                scope=pyrogram.types.BotCommandScopeAllGroupChats(),
            )
            await self.set_bot_commands(
                make_commands(public_commands + owner_commands),
                scope=pyrogram.types.BotCommandScopeChat(chat_id=self.owner),
            )
            logger.info("Telegram slash-command menus registered.")
        except Exception:
            logger.exception("Failed to register Telegram slash-command menus.")

    async def boot(self):
        """
        Starts the bot and performs initial setup.

        Raises:
            SystemExit: If the bot fails to access the log group or is not an administrator in the logger group.
        """
        await super().start()
        self.id = self.me.id
        self.name = self.me.first_name
        self.username = self.me.username
        self.mention = self.me.mention
        await self._register_command_menu()

        try:
            await self.send_message(self.logger, "Bot Started")
            get = await self.get_chat_member(self.logger, self.id)
        except Exception as ex:
            raise SystemExit(f"Bot has failed to access the log group: {self.logger}\nReason: {ex}")

        if get.status != pyrogram.enums.ChatMemberStatus.ADMINISTRATOR:
            raise SystemExit("Please promote the bot as an admin in logger group.")
        logger.info(f"Bot started as @{self.username}")

    async def exit(self):
        """
        Asynchronously stops the bot.
        """
        await super().stop()
        logger.info("Bot stopped.")
