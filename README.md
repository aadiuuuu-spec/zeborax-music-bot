# ZeboraX Music Bot

Telegram bot project maintained by **Aditya**.

- Bot: [@ZeboraXmusic_bot](https://t.me/ZeboraXmusic_bot)
- Owner: [@II_YUTA_II](https://t.me/II_YUTA_II)

## Branch status

This `go-rebuild` branch contains the first Go control-plane scaffold. It is intentionally separate from the existing Python deployment on `main`.

Implemented in this scaffold:
- Telegram bot startup using `BOT_TOKEN`
- Private-chat and group command responses for `/start` and `/help`
- Command parsing for the planned music controls
- HTTP health endpoint at `/health`
- Graceful shutdown and a multi-stage Go Dockerfile

**Not implemented yet:** actual Telegram voice-chat joining, assistant user session, audio streaming, song search, queue persistence, and playback controls. The music commands explicitly report that playback is not connected; they do not pretend to play audio.

## Build locally

Requires Go 1.22 or newer.

```sh
go mod tidy
go build ./cmd/bot
BOT_TOKEN="your-token" ./bot
```

## Deploying this branch

Use `Dockerfile.go` as the Dockerfile path in the deployment service. Set `BOT_TOKEN` in the hosting provider's secret environment variables. The service exposes `/health` on the platform-provided `PORT`.

Do not commit real tokens, API hashes, or session strings. Never send them in chat. Rotate a credential immediately if it is exposed.

## Planned voice engine

A Telegram bot token alone cannot join a group voice chat as an assistant user. A separate Telegram user-account session and a compatible voice-call engine will be needed for that feature. Add any session string only as a private deployment secret after the voice engine is implemented and tested.

## Audio and platform policy

Playback will be limited to audio the operator owns, is licensed to use, or is otherwise authorized to stream. This project will not use browser cookies or account sessions to bypass another platform's access controls.
