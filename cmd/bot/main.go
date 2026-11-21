package main

import (
	"context"
	"html"
	"fmt"
	"log"
	"net/http"
	"net/url"
	"os"
	"os/signal"
	"strconv"
	"strings"
	"syscall"
	"time"

	"github.com/aadiuuuu-spec/zeborax-music-bot/internal/catalog"
	"github.com/aadiuuuu-spec/zeborax-music-bot/internal/music"
	"github.com/aadiuuuu-spec/zeborax-music-bot/internal/voice"
	"github.com/go-telegram/bot"
	"github.com/go-telegram/bot/models"
)

var queues *music.Manager
var voiceEngine *voice.Engine

func main() {
	token := strings.TrimSpace(os.Getenv("BOT_TOKEN"))
	if token == "" { log.Fatal("BOT_TOKEN is required") }
	var err error
	queues, err = music.New(envOr("QUEUE_STATE_FILE", "data/queues.json"))
	if err != nil { log.Fatalf("load queue state: %v", err) }

	voiceEngine, err = voice.NewFromEnv()
	if err != nil {
		if err == voice.ErrNotConfigured {
			log.Println("Voice engine disabled: configure API_ID, API_HASH and ASSISTANT_SESSION as private deployment variables")
		} else { log.Fatalf("initialize voice engine: %v", err) }
	} else {
		log.Println("Telegram assistant voice engine initialized")
	}

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	b, err := bot.New(token, bot.WithDefaultHandler(handleMessage))
	if err != nil { log.Fatalf("create Telegram bot: %v", err) }

	mux := http.NewServeMux()
	mux.HandleFunc("/health", func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte("{\"status\":\"ok\",\"service\":\"zeborax-bot\"}"))
	})
	port := strings.TrimSpace(envOr("PORT", "8080"))
	addr := port
	if !strings.Contains(port, ":") {
		addr = ":" + port
	}
	server := &http.Server{Addr: addr, Handler: mux, ReadHeaderTimeout: 5 * time.Second}
	go func() {
		log.Printf("health server listening on %s", addr)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Printf("health server: %v", err)
			stop()
		}
	}()

	log.Println("ZeboraX Go bot starting; Telegram long polling enabled")
	go b.Start(ctx)
	<-ctx.Done()
	if voiceEngine != nil { voiceEngine.Close() }
	shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	_ = server.Shutdown(shutdownCtx)
	log.Println("ZeboraX stopped")
}

func handleMessage(ctx context.Context, b *bot.Bot, update *models.Update) {
	if update.Message == nil || update.Message.Text == "" { return }
	msg := update.Message
	parts := strings.Fields(strings.TrimSpace(msg.Text))
	if len(parts) == 0 { return }
	command := strings.ToLower(strings.SplitN(parts[0], "@", 2)[0])
	args := parts[1:]
	chatID := msg.Chat.ID
	reply := ""
	switch command {
	case "/start":
		reply = "ZeboraX Music Bot is online. Use /help to see commands."
	case "/help":
		reply = "ZeboraX commands:\n/play <song name> — search full-length licensed tracks (assistant auto-joins)\n/play <public audio URL> — stream an authorized audio URL\n/join — join this group's active voice chat\n/queue — show saved text requests\n/pause /resume /skip\n/stop — stop audio and clear requests\n/end — leave voice chat\n/volume 1-200\n/shuffle /loop /autoplay\n\nSong-name search uses Jamendo's full-length catalog and only plays CC0, CC BY, or CC BY-SA tracks. Tracks without an accepted license or a working stream are skipped."
	case "/join":
		if voiceEngine == nil { reply = voiceSetupHint(); break }
		if err := voiceEngine.Join(chatID); err != nil { reply = "Could not join voice chat: " + err.Error() } else { reply = "Assistant joined the active voice chat." }
	case "/play":
		if len(args) == 0 { reply = "Usage: /play <song name or authorized audio URL>"; break }
		if voiceEngine == nil { reply = voiceSetupHint(); break }
		raw := strings.Join(args, " ")
		u, parseErr := url.ParseRequestURI(raw)
		if parseErr == nil && (u.Scheme == "http" || u.Scheme == "https") && u.Host != "" {
			if err := voiceEngine.PlayURL(ctx, chatID, raw); err != nil { reply = "Playback could not start: " + err.Error() } else { reply = "Audio stream started in the voice chat." }
			break
		}
		clientID := strings.TrimSpace(os.Getenv("JAMENDO_CLIENT_ID"))
		if clientID == "" {
			reply = "Full-song search is not configured yet. Add JAMENDO_CLIENT_ID as a private deployment variable. Song search will not fall back to short previews."
			break
		}
		results, err := catalog.SearchLicensed(ctx, raw, clientID)
		if err != nil {
			reply = "No authorized full-length track found: " + err.Error()
			break
		}
		var failures []string
		played := false
		for _, track := range results {
			if err := voiceEngine.PlayURL(ctx, chatID, track.StreamURL); err != nil {
				failures = append(failures, track.Title+": "+err.Error())
				continue
			}
			reply = fmt.Sprintf("▶ Now playing full track: %s — %s\nLicense: %s\nSource: Jamendo. Assistant joined the voice chat automatically.", track.Title, track.Artist, track.License)
			played = true
			break
		}
		if !played {
			reply = "All matching licensed tracks failed to start. Try another search.\n" + strings.Join(failures, "\n")
		}
	case "/queue":
		state := queues.Snapshot(chatID)
		if len(state.Queue) == 0 { reply = "Queue is empty."; break }
		var lines []string
		for i, track := range state.Queue {
			if i == 20 { lines = append(lines, fmt.Sprintf("…and %d more", len(state.Queue)-20)); break }
			lines = append(lines, fmt.Sprintf("%d. %s", i+1, track.Query))
		}
		reply = "Saved requests:\n" + strings.Join(lines, "\n")
	case "/pause":
		if voiceEngine == nil { reply = voiceSetupHint() } else if err := voiceEngine.Pause(chatID); err != nil { reply = err.Error() } else { reply = "Playback paused." }
	case "/resume":
		if voiceEngine == nil { reply = voiceSetupHint() } else if err := voiceEngine.Resume(chatID); err != nil { reply = err.Error() } else { reply = "Playback resumed." }
	case "/skip":
		if voiceEngine == nil { reply = voiceSetupHint() } else if err := voiceEngine.Skip(chatID); err != nil { reply = err.Error() } else { reply = "Current track skipped." }
	case "/stop":
		if voiceEngine != nil { voiceEngine.Stop(chatID) }
		if err := queues.Clear(chatID); err != nil { reply = "Could not clear saved requests: " + err.Error() } else { reply = "Playback stopped and saved requests cleared." }
	case "/end":
		if voiceEngine == nil { reply = voiceSetupHint() } else if err := voiceEngine.Leave(chatID); err != nil { reply = "Could not leave voice chat: " + err.Error() } else { reply = "Assistant left the voice chat." }
	case "/shuffle":
		enabled, err := queues.ToggleShuffle(chatID)
		if err != nil { reply = "Could not shuffle queue: " + err.Error() } else { reply = fmt.Sprintf("Queue shuffle %s.", onOff(enabled)) }
	case "/loop":
		mode := "track"; if len(args) > 0 { mode = strings.ToLower(args[0]) }
		if err := queues.SetLoop(chatID, mode); err != nil { reply = "Usage: /loop off|track|queue" } else { reply = "Loop preference set to " + mode + "." }
	case "/autoplay":
		enabled, err := queues.ToggleAutoplay(chatID)
		if err != nil { reply = "Could not update autoplay: " + err.Error() } else { reply = fmt.Sprintf("Autoplay preference %s. Search provider is not configured for recommendations.", onOff(enabled)) }
	case "/volume":
		if len(args) != 1 { reply = "Usage: /volume 1-200"; break }
		value, err := strconv.Atoi(args[0])
		if err != nil || value < 1 || value > 200 { reply = "Volume must be a number from 1 to 200."; break }
		if err := queues.SetVolume(chatID, value); err != nil { reply = "Could not save volume: " + err.Error(); break }
		if voiceEngine == nil { reply = fmt.Sprintf("Saved volume preference: %d%%. %s", value, voiceSetupHint()) } else if err := voiceEngine.SetVolume(chatID, value); err != nil { reply = fmt.Sprintf("Saved volume preference: %d%%. %s", value, err.Error()) } else { reply = fmt.Sprintf("Volume set to %d%%.", value) }
	default:
		return
	}
	if _, err := b.SendMessage(ctx, &bot.SendMessageParams{ChatID: chatID, Text: formatReply(reply), ParseMode: "HTML"}); err != nil { log.Printf("send message: %v", err) }
}

// formatReply adds consistent Telegram HTML emphasis while escaping user/provider text.
func formatReply(reply string) string {
	parts := strings.SplitN(html.EscapeString(strings.TrimSpace(reply)), "\n", 2)
	if len(parts) == 0 || parts[0] == "" { return "🎵 <b>ZeboraX Music</b>" }
	if len(parts) == 1 { return "🎵 <b>" + parts[0] + "</b>" }
	return "🎵 <b>" + parts[0] + "</b>\n" + parts[1]
}

func voiceSetupHint() string {
	return "Voice engine is not configured. Add API_ID, API_HASH and ASSISTANT_SESSION as private deployment variables. Never paste a session string into chat or commit it."
}
func onOff(enabled bool) string { if enabled { return "enabled" }; return "disabled" }
func envOr(key, fallback string) string {
	if value := strings.TrimSpace(os.Getenv(key)); value != "" { return value }
	return fallback
}
