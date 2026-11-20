# ZeboraX Music Bot

Telegram bot project maintained by **Aditya**.

- Bot: [@ZeboraXmusic_bot](https://t.me/ZeboraXmusic_bot)
- Owner: [@II_YUTA_II](https://t.me/II_YUTA_II)

## Current Go rebuild status

This `go-rebuild` branch is separate from the original Python `main` branch.

Implemented:
- Telegram bot startup and graceful shutdown
- Private and group `/start` and `/help`
- Per-chat request queue with JSON persistence
- `/play` stores a text request; `/queue` lists saved requests
- `/shuffle`, `/loop`, `/autoplay`, and `/volume` queue preferences
- `/stop` and `/end` clear the saved queue
- `/health` endpoint and GitHub Actions Go checks

Not implemented:
- Telegram voice-chat assistant login and joining
- Actual audio streaming, pause/resume/skip of a live stream
- Song search, recommendations, and media-source integration

The bot clearly reports these limitations. A saved `/play` request is currently a queued text request, not a playing song.

## Build and run

Requires Go 1.22 or newer.

```sh
go mod tidy
go test ./...
go build ./cmd/bot
BOT_TOKEN="your-token" ./bot
```

## Railway deployment

Set the service Dockerfile path to `Dockerfile.go`. Add `BOT_TOKEN` as a private Railway Variable. The health endpoint listens on the platform-provided `PORT`.

For queue persistence across redeploys, attach a Railway Volume mounted at `/app/data`. Without a persistent volume, queue state may be lost when the container is replaced.

## Secrets

Never commit or send bot tokens, API hashes, Telegram session strings, or cookies. Store credentials only in private deployment variables. Rotate any credential that is exposed.

## Voice engine and audio policy

A Telegram bot token alone cannot join a group voice chat as an assistant user. A separate Telegram user-account session and a compatible voice-call engine are required. Add a session string only as a private deployment secret after the voice engine has been implemented and tested.

Playback will be limited to audio the operator owns, is licensed to use, or is otherwise authorized to stream. This project will not use browser cookies or account sessions to bypass another platform's access controls.
