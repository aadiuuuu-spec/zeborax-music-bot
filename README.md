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
- `/play <song name>` searches Apple's public iTunes Search API and streams the first available audio preview
- Assistant automatically joins the active group voice chat when preview playback starts
- `/play <public audio URL>` streams an authorized HTTP/HTTPS audio URL through FFmpeg
- Pause, resume, skip, stop and volume controls for the active stream
- Per-chat saved text-request queue and JSON persistence

### Important playback limitation
The public iTunes Search API supplies short preview clips, not full-length songs. This implementation therefore proves the search-to-voice-chat flow, but it is not a full-song catalog. Full-length playback requires a music provider that explicitly authorizes streaming and provides a supported playback API. Search metadata alone is not an audio stream. YouTube cookie extraction or account-session access bypasses are not included.

Queue auto-advance and autoplay recommendations are not implemented yet. A real Telegram group voice-chat end-to-end test and Go CI build are still required before calling this production-ready.

## Environment variables

Set these as private Railway Variables (never commit them):

- `BOT_TOKEN` — BotFather bot token
- `API_ID` — Telegram application ID
- `API_HASH` — Telegram application hash
- `ASSISTANT_SESSION` — MTProto session for a separate assistant account
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
