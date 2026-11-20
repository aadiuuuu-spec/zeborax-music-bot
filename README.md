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
- Audio-only streaming from a public HTTP/HTTPS media URL through ffmpeg
- Pause, resume, skip, stop and volume controls for the active stream
- Per-chat saved text-request queue and queue preferences
- JSON queue persistence

### Still not implemented
- Song-name search and a supported catalog/provider
- Automatic next-track queue playback and autoplay recommendations
- A verified end-to-end live voice-chat test against a real Telegram group

A plain `/play song name` is saved as a text request; it does not magically search or play. To stream now, use `/play https://.../audio-file.mp3` with a public audio URL you are authorized to use. YouTube cookie extraction or account-session access bypasses are not included.

## Environment variables

Set these as private Railway Variables (never commit them):

- `BOT_TOKEN` — BotFather bot token
- `API_ID` — Telegram application ID
- `API_HASH` — Telegram application hash
- `ASSISTANT_SESSION` — MTProto session for a separate assistant account
- `PORT` — supplied by Railway
- `QUEUE_STATE_FILE` — defaults to `/app/data/queues.json` in Docker

Use a separate assistant account that you control and can afford to dedicate to this bot. A Telegram session can grant access to that account. Never paste it into a chat, issue, commit, screenshot, or public log. If it is exposed, revoke that session from Telegram's active sessions immediately.

The assistant account must be a member of the group, and the group must already have an active voice chat for `/join` to work.

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
