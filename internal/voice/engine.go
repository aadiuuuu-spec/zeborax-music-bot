package voice

import (
	"context"
	"errors"
	"fmt"
	"net"
	"net/url"
	"os"
	"strconv"
	"strings"
	"sync"

	"github.com/amarnathcjd/gogram/telegram"
	"github.com/amarnathcjd/gortc"
)

var ErrNotConfigured = errors.New("voice engine is not configured")

type Engine struct {
	client *telegram.Client
	mu sync.Mutex
	calls map[int64]*gortc.Call
	players map[int64]*gortc.Player
}

func NewFromEnv() (*Engine, error) {
	rawID := strings.TrimSpace(os.Getenv("API_ID"))
	apiHash := strings.TrimSpace(os.Getenv("API_HASH"))
	session := strings.TrimSpace(os.Getenv("ASSISTANT_SESSION"))
	if rawID == "" || apiHash == "" || session == "" {
		return nil, ErrNotConfigured
	}
	id, err := strconv.ParseInt(rawID, 10, 32)
	if err != nil || id <= 0 {
		return nil, fmt.Errorf("API_ID must be a positive integer")
	}
	client, err := telegram.NewClient(telegram.ClientConfig{
		AppID: int32(id),
		AppHash: apiHash,
		StringSession: session,
		MemorySession: true,
	})
	if err != nil {
		return nil, fmt.Errorf("create assistant client: %w", err)
	}
	client.Conn()
	return &Engine{client: client, calls: make(map[int64]*gortc.Call), players: make(map[int64]*gortc.Player)}, nil
}

func (e *Engine) Join(chatID int64) error {
	e.mu.Lock()
	defer e.mu.Unlock()
	if e.calls[chatID] != nil {
		return nil
	}
	call := gortc.NewCall(e.client)
	if err := call.Join(chatID); err != nil {
		return fmt.Errorf("join group voice chat: %w", err)
	}
	e.calls[chatID] = call
	return nil
}

func (e *Engine) PlayURL(ctx context.Context, chatID int64, rawURL string) error {
	u, err := url.ParseRequestURI(strings.TrimSpace(rawURL))
	if err != nil || (u.Scheme != "https" && u.Scheme != "http") || u.Hostname() == "" {
		return errors.New("use a valid public HTTP or HTTPS audio URL")
	}
	host := u.Hostname()
	if ip := net.ParseIP(host); ip != nil && (ip.IsPrivate() || ip.IsLoopback() || ip.IsLinkLocalUnicast() || ip.IsUnspecified()) {
		return errors.New("private or local network URLs are not allowed")
	}
	if err := e.Join(chatID); err != nil {
		return err
	}
	e.mu.Lock()
	call := e.calls[chatID]
	if old := e.players[chatID]; old != nil {
		old.Stop()
	}
	player := call.Play(ctx, gortc.FromURL(u.String(), gortc.EncodeOptions{Tracks: gortc.TrackAudio}))
	if player == nil {
		e.mu.Unlock()
		return errors.New("voice player could not be started")
	}
	e.players[chatID] = player
	e.mu.Unlock()

	go func() {
		<-player.Done()
		e.mu.Lock()
		if e.players[chatID] == player {
			delete(e.players, chatID)
		}
		e.mu.Unlock()
	}()
	return nil
}

func (e *Engine) Pause(chatID int64) error {
	e.mu.Lock()
	defer e.mu.Unlock()
	p := e.players[chatID]
	if p == nil { return errors.New("nothing is playing") }
	p.Pause()
	return nil
}

func (e *Engine) Resume(chatID int64) error {
	e.mu.Lock()
	defer e.mu.Unlock()
	p := e.players[chatID]
	if p == nil { return errors.New("nothing is playing") }
	p.Resume()
	return nil
}

func (e *Engine) Skip(chatID int64) error {
	e.mu.Lock()
	defer e.mu.Unlock()
	p := e.players[chatID]
	if p == nil { return errors.New("nothing is playing") }
	p.Stop()
	delete(e.players, chatID)
	return nil
}

func (e *Engine) Stop(chatID int64) {
	e.mu.Lock()
	defer e.mu.Unlock()
	if p := e.players[chatID]; p != nil { p.Stop(); delete(e.players, chatID) }
}

func (e *Engine) SetVolume(chatID int64, volume int) error {
	e.mu.Lock()
	defer e.mu.Unlock()
	call := e.calls[chatID]
	if call == nil { return errors.New("assistant is not in this voice chat; use /join first") }
	return call.SetVolume(volume)
}

func (e *Engine) Leave(chatID int64) error {
	e.mu.Lock()
	defer e.mu.Unlock()
	if p := e.players[chatID]; p != nil { p.Stop(); delete(e.players, chatID) }
	call := e.calls[chatID]
	if call == nil { return nil }
	delete(e.calls, chatID)
	return call.Leave()
}

func (e *Engine) Close() {
	e.mu.Lock()
	defer e.mu.Unlock()
	for id, p := range e.players { p.Stop(); delete(e.players, id) }
	for id, call := range e.calls { _ = call.Leave(); delete(e.calls, id) }
	if e.client != nil { _ = e.client.Disconnect() }
}
