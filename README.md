# ZeboraX Music Bot

Telegram group voice-chat music bot maintained by **Aditya**.

- Bot username: [@ZeboraXmusic_bot](https://t.me/ZeboraXmusic_bot)
- Owner: [@II_YUTA_II](https://t.me/II_YUTA_II)

## Features

- Play audio files sent in a Telegram group or by replying with `/play`
- Pause, resume, skip, queue, shuffle
- Loop modes: off, current track, queue
- Autoplay toggle (repeats the current track when the queue becomes empty)
- Volume command
- `/end` stops playback and leaves the voice chat

## Requirements

- Python 3.10+
- Telegram API ID and API hash
- A Telegram bot token from BotFather
- A user-account Pyrogram session string for the voice-chat assistant
- A Railway service using the included Dockerfile

**Important:** Telegram voice chats require an MTProto user account to join. The bot token alone cannot join a voice chat. Keep the assistant account dedicated to this bot and protect its session string like a password.

## Railway deployment

1. Create a Railway project and deploy this GitHub repository.
2. Add these variables in Railway service Variables:
   - `API_ID`
   - `API_HASH`
   - `BOT_TOKEN`
   - `SESSION_STRING`
   - `OWNER_USERNAME` = `II_YUTA_II`
3. Deploy/redeploy and check the service logs.

Do not put real credentials in GitHub. Use Railway Variables only. Railway usage may incur charges; check the current plan and estimated usage before deploying.

## Use

1. Add the bot and the assistant account to your Telegram group.
2. Make the assistant account an admin if Telegram requires it to manage/join the group voice chat.
3. Start a group voice chat.
4. Send an audio file in the group, or reply to an audio file with `/play`.
5. Use `/help` to see commands.

The Telegram Bot API download limit means this starter accepts audio files up to 20 MB.

## Legal use

Only play audio that you own, have permission to use, or that is otherwise legally available to you. This project does not download music from YouTube or other third-party platforms.

## Current scope

This is an initial implementation scaffold, not a promise of 24/7 free hosting. Test it in a private group first. Some Telegram voice-chat permissions and PyTgCalls compatibility may require adjustments for your account and group.
