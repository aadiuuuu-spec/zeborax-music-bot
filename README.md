# ZeboraX Music Bot

Telegram music bot project maintained by **Aditya**.

- Bot: [@ZeboraXmusic_bot](https://t.me/ZeboraXmusic_bot)
- Owner: [@II_YUTA_II](https://t.me/II_YUTA_II)

## Go rebuild

This branch is separate from the original Python `main` branch.

### Implemented in this branch
- Telegram Bot API command handling and health endpoint
- Telegram MTProto assistant client configuration
- Group voice-chat join/leave via gortc
- `/play <song name>` searches Jamendo for full-length tracks and only accepts CC0, CC BY, or CC BY-SA licenses
- The bot skips results with an unsupported license or failed stream and tries the next matching result
- Assistant automatically joins the active group voice chat when a full-track stream starts
- `/play <public audio URL>` streams an authorized HTTP/HTTPS audio URL through FFmpeg
- Pause, resume, skip, stop and volume controls for the active stream
- Per-chat saved text-request queue and JSON persistence

### Important playback limitation
Song-name search uses Jamendo's catalog, which provides full-length streams for independent music published under Creative Commons licenses. The bot conservatively accepts only CC0, CC BY, and CC BY-SA licenses, and includes the license link in its now-playing message. This catalog will not contain every mainstream/commercial song. A missing or failed result is skipped; it does not fall back to a short preview. Review Jamendo's API terms and each track's license before using the bot in a public or commercial setting. YouTube cookie extraction or account-session access bypasses are not included.

Queue auto-advance and autoplay recommendations are not implemented yet. A real Telegram group voice-chat end-to-end test and Go CI build are still required before calling this production-ready.

## Environment variables

Set these as private Railway Variables (never commit them):

- `BOT_TOKEN` — BotFather bot token
- `API_ID` — Telegram application ID
- `API_HASH` — Telegram application hash
- `ASSISTANT_SESSION` — MTProto session for a separate assistant account
- `JAMENDO_CLIENT_ID` — application client ID from your Jamendo developer account (required for full-track song-name search)
- `PORT` — supplied by Railway
- `QUEUE_STATE_FILE` — defaults to `/app/data/queues.json` in Docker

Use a separate assistant account that you control and can afford to dedicate to this bot. A Telegram session can grant access to that account. Never paste it into a chat, issue, commit, screenshot, or public log. If it is exposed, revoke that session from Telegram's active sessions immediately.

The assistant account must be a member of the group, and the group must already have an active voice chat for playback to work.

## Build and test

Requires Go 1.26+, ffmpeg at runtime.

```sh
go mod tidy
go test ./...
go build ./cmd/bot
```

For Railway, set the service Dockerfile path to `Dockerfile.go`. Attach a persistent Volume at `/app/data` if queue state must survive redeploys.

## Licensing

The voice integration uses gortc (MIT) and gogram (GPL-3.0). Review and comply with the GPL-3.0 terms when distributing builds that include gogram. Preserve upstream notices and license texts.
