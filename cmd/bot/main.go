package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"strconv"
	"strings"
	"syscall"
	"time"

	"github.com/aadiuuuu-spec/zeborax-music-bot/internal/music"
	"github.com/go-telegram/bot"
	"github.com/go-telegram/bot/models"
)

var queues *music.Manager

func main() {
	token := strings.TrimSpace(os.Getenv("BOT_TOKEN"))
	if token == "" {
		log.Fatal("BOT_TOKEN is required")
	}
	var err error
	queues, err = music.New(envOr("QUEUE_STATE_FILE", "data/queues.json"))
	if err != nil {
		log.Fatalf("load queue state: %v", err)
	}

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	b, err := bot.New(token, bot.WithDefaultHandler(handleMessage))
	if err != nil {
		log.Fatalf("create Telegram bot: %v", err)
	}

	mux := http.NewServeMux()
	mux.HandleFunc("/health", func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte("{\"status\":\"ok\",\"service\":\"zeborax-bot\"}"))
	})
	server := &http.Server{Addr: envOr("PORT", "8080"), Handler: mux, ReadHeaderTimeout: 5 * time.Second}
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
	msg := update.Message
	parts := strings.Fields(strings.TrimSpace(msg.Text))
	if len(parts) == 0 {
		return
	}
	command := strings.ToLower(strings.SplitN(parts[0], "@", 2)[0])
	args := parts[1:]
	chatID := msg.Chat.ID
	requester := "Telegram user"
	if msg.From != nil {
		if msg.From.Username != "" {
			requester = "@" + msg.From.Username
		} else {
			requester = msg.From.FirstName
		}
	}

	reply := ""
	switch command {
	case "/start":
		reply = "ZeboraX Music Bot is online. Use /help to see commands."
	case "/help":
		reply = "ZeboraX commands:\n/play <song name> — add a request to the queue\n/queue — show queued requests\n/pause and /resume — require active playback\n/skip — skip current track\n/stop or /end — clear queue\n/shuffle — toggle queue shuffle\n/loop off|track|queue\n/autoplay — toggle autoplay\n/volume 1-200\n\nQueue management is active. Voice-chat streaming and song search are not connected yet."
	case "/play":
		if len(args) == 0 {
			reply = "Usage: /play <song name>"
			break
		}
		position, err := queues.Add(chatID, strings.Join(args, " "), requester)
		if err != nil {
			reply = "Could not save request: " + err.Error()
		} else {
			reply = fmt.Sprintf("Added to queue at position %d. Voice playback is not connected yet, so this request is saved but not playing.", position)
		}
	case "/queue":
		state := queues.Snapshot(chatID)
		if len(state.Queue) == 0 {
			reply = "Queue is empty."
			break
		}
		var lines []string
		for i, track := range state.Queue {
			if i == 20 {
				lines = append(lines, fmt.Sprintf("…and %d more", len(state.Queue)-20))
				break
			}
			lines = append(lines, fmt.Sprintf("%d. %s", i+1, track.Query))
		}
		reply = "Upcoming requests:\n" + strings.Join(lines, "\n")
	case "/pause", "/resume":
		paused := command == "/pause"
		if err := queues.SetPaused(chatID, paused); err != nil {
			reply = "No active track. Voice playback engine is not connected yet."
		} else if paused {
			reply = "Playback paused."
		} else {
			reply = "Playback resumed."
		}
	case "/skip":
		reply = "Skip is unavailable until the voice-chat playback engine is connected."
	case "/stop", "/end":
		if err := queues.Clear(chatID); err != nil {
			reply = "Could not clear queue: " + err.Error()
		} else {
			reply = "Queue cleared. No voice call was active in this build."
		}
	case "/shuffle":
		enabled, err := queues.ToggleShuffle(chatID)
		if err != nil {
			reply = "Could not shuffle queue: " + err.Error()
		} else if enabled {
			reply = "Queue shuffle enabled."
		} else {
			reply = "Queue shuffle disabled."
		}
	case "/loop":
		mode := "track"
		if len(args) > 0 {
			mode = strings.ToLower(args[0])
		}
		if err := queues.SetLoop(chatID, mode); err != nil {
			reply = "Usage: /loop off|track|queue"
		} else {
			reply = "Loop mode set to " + mode + ". It will apply when playback is implemented."
		}
	case "/autoplay":
		enabled, err := queues.ToggleAutoplay(chatID)
		if err != nil {
			reply = "Could not update autoplay: " + err.Error()
		} else {
			reply = fmt.Sprintf("Autoplay %s. Recommendations are not connected yet.", onOff(enabled))
		}
	case "/volume":
		if len(args) != 1 {
			reply = "Usage: /volume 1-200"
			break
		}
		value, err := strconv.Atoi(args[0])
		if err != nil || queues.SetVolume(chatID, value) != nil {
			reply = "Volume must be a number from 1 to 200."
		} else {
			reply = fmt.Sprintf("Volume preference saved: %d%%. It will apply when playback is connected.", value)
		}
	default:
		return
	}

	if _, err := b.SendMessage(ctx, &bot.SendMessageParams{ChatID: chatID, Text: reply}); err != nil {
		log.Printf("send message: %v", err)
	}
}

func onOff(enabled bool) string {
	if enabled { return "enabled" }
	return "disabled"
}

func envOr(key, fallback string) string {
	if value := strings.TrimSpace(os.Getenv(key)); value != "" {
		return value
	}
	return fallback
}
