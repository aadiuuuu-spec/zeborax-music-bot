package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"github.com/go-telegram/bot"
	"github.com/go-telegram/bot/models"
)

func main() {
	token := strings.TrimSpace(os.Getenv("BOT_TOKEN"))
	if token == "" {
		log.Fatal("BOT_TOKEN is required")
	}

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	opts := []bot.Option{
		bot.WithDefaultHandler(handleMessage),
	}
	b, err := bot.New(token, opts...)
	if err != nil {
		log.Fatalf("create Telegram bot: %v", err)
	}

	mux := http.NewServeMux()
	mux.HandleFunc("/health", func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte("{\"status\":\"ok\",\"service\":\"zeborax-bot\"}"))
	})
	server := &http.Server{
		Addr:              envOr("PORT", "8080"),
		Handler:           mux,
		ReadHeaderTimeout: 5 * time.Second,
	}
	go func() {
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Printf("health server: %v", err)
			stop()
		}
	}()

	log.Println("ZeboraX Go bot starting")
	go b.Start(ctx)
	<-ctx.Done()

	shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	_ = server.Shutdown(shutdownCtx)
	log.Println("ZeboraX stopped")
}

func handleMessage(ctx context.Context, b *bot.Bot, update *models.Update) {
	if update.Message == nil || update.Message.Text == "" {
		return
	}
	text := strings.TrimSpace(update.Message.Text)
	parts := strings.Fields(text)
	if len(parts) == 0 {
		return
	}
	command := strings.ToLower(strings.SplitN(parts[0], "@", 2)[0])
	var reply string

	switch command {
	case "/start":
		reply = "ZeboraX Music Bot is online. Use /help to see commands."
	case "/help":
		reply = "ZeboraX commands:\n/play <song name>\n/pause\n/resume\n/skip\n/queue\n/stop\n/end\n/shuffle\n/loop\n/autoplay\n/volume <1-200>\n\nVoice playback engine is not connected yet; this build currently handles bot commands and health checks."
	case "/play":
		if len(parts) < 2 {
			reply = "Usage: /play <song name>"
		} else {
			reply = "Song request received: " + strings.Join(parts[1:], " ") + ". Playback provider is not configured yet."
		}
	case "/pause", "/resume", "/skip", "/queue", "/stop", "/end", "/shuffle", "/loop", "/autoplay", "/volume":
		reply = "This command is registered, but voice-chat playback is not connected in this build yet."
	default:
		return
	}

	if _, err := b.SendMessage(ctx, &bot.SendMessageParams{
		ChatID: update.Message.Chat.ID,
		Text:   reply,
	}); err != nil {
		log.Printf("send message: %v", err)
	}
}

func envOr(key, fallback string) string {
	if value := strings.TrimSpace(os.Getenv(key)); value != "" {
		return value
	}
	return fallback
}
