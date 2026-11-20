package music

import (
	"encoding/json"
	"errors"
	"fmt"
	"math/rand"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"
)

var (
	ErrEmptyQuery = errors.New("song query is empty")
	ErrEmptyQueue = errors.New("queue is empty")
	ErrNoTrack    = errors.New("no track is currently selected")
)

type Track struct {
	Query     string    `json:"query"`
	Requested string    `json:"requested_by,omitempty"`
	AddedAt   time.Time `json:"added_at"`
}

type ChatState struct {
	Current  *Track  `json:"current,omitempty"`
	Queue    []Track `json:"queue"`
	Paused   bool    `json:"paused"`
	Loop     string  `json:"loop"` // off, track, queue
	Autoplay bool    `json:"autoplay"`
	Shuffle  bool    `json:"shuffle"`
	Volume   int     `json:"volume"`
}

type diskState struct {
	Version int                  `json:"version"`
	Chats   map[int64]*ChatState `json:"chats"`
}

type Manager struct {
	mu    sync.RWMutex
	path  string
	chats map[int64]*ChatState
	rng   *rand.Rand
}

func New(path string) (*Manager, error) {
	m := &Manager{
		path:  path,
		chats: make(map[int64]*ChatState),
		rng:   rand.New(rand.NewSource(time.Now().UnixNano())),
	}
	if path == "" {
		return m, nil
	}
	data, err := os.ReadFile(path)
	if errors.Is(err, os.ErrNotExist) {
		return m, nil
	}
	if err != nil {
		return nil, fmt.Errorf("read queue state: %w", err)
	}
	var saved diskState
	if err := json.Unmarshal(data, &saved); err != nil {
		return nil, fmt.Errorf("decode queue state: %w", err)
	}
	if saved.Chats != nil {
		m.chats = saved.Chats
	}
	for id, state := range m.chats {
		if state == nil {
			delete(m.chats, id)
			continue
		}
		if state.Queue == nil {
			state.Queue = []Track{}
		}
		if state.Volume < 1 || state.Volume > 200 {
			state.Volume = 100
		}
		if state.Loop != "track" && state.Loop != "queue" {
			state.Loop = "off"
		}
		// A process restart cannot safely resume a live voice call.
		state.Paused = false
	}
	return m, nil
}

func (m *Manager) state(id int64) *ChatState {
	s := m.chats[id]
	if s == nil {
		s = &ChatState{Queue: []Track{}, Loop: "off", Volume: 100}
		m.chats[id] = s
	}
	return s
}

func (m *Manager) persistLocked() error {
	if m.path == "" {
		return nil
	}
	if err := os.MkdirAll(filepath.Dir(m.path), 0700); err != nil {
		return err
	}
	data, err := json.MarshalIndent(diskState{Version: 1, Chats: m.chats}, "", "  ")
	if err != nil {
		return err
	}
	tmp := m.path + ".tmp"
	if err := os.WriteFile(tmp, data, 0600); err != nil {
		return err
	}
	if err := os.Rename(tmp, m.path); err != nil {
		_ = os.Remove(tmp)
		return err
	}
	return nil
}

func (m *Manager) Add(id int64, query, requestedBy string) (int, error) {
	query = strings.TrimSpace(query)
	if query == "" {
		return 0, ErrEmptyQuery
	}
	m.mu.Lock()
	defer m.mu.Unlock()
	s := m.state(id)
	s.Queue = append(s.Queue, Track{Query: query, Requested: requestedBy, AddedAt: time.Now().UTC()})
	if err := m.persistLocked(); err != nil {
		s.Queue = s.Queue[:len(s.Queue)-1]
		return 0, err
	}
	return len(s.Queue), nil
}

func (m *Manager) Snapshot(id int64) ChatState {
	m.mu.RLock()
	defer m.mu.RUnlock()
	s := m.chats[id]
	if s == nil {
		return ChatState{Queue: []Track{}, Loop: "off", Volume: 100}
	}
	cp := *s
	cp.Queue = append([]Track(nil), s.Queue...)
	if s.Current != nil {
		current := *s.Current
		cp.Current = &current
	}
	return cp
}

func (m *Manager) SetPaused(id int64, paused bool) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	s := m.state(id)
	if s.Current == nil {
		return ErrNoTrack
	}
	old := s.Paused
	s.Paused = paused
	if err := m.persistLocked(); err != nil {
		s.Paused = old
		return err
	}
	return nil
}

func (m *Manager) SetLoop(id int64, mode string) error {
	if mode != "off" && mode != "track" && mode != "queue" {
		return fmt.Errorf("loop mode must be off, track, or queue")
	}
	m.mu.Lock()
	defer m.mu.Unlock()
	s := m.state(id)
	old := s.Loop
	s.Loop = mode
	if err := m.persistLocked(); err != nil {
		s.Loop = old
		return err
	}
	return nil
}

func (m *Manager) ToggleAutoplay(id int64) (bool, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	s := m.state(id)
	old := s.Autoplay
	s.Autoplay = !s.Autoplay
	if err := m.persistLocked(); err != nil {
		s.Autoplay = old
		return false, err
	}
	return s.Autoplay, nil
}

func (m *Manager) SetVolume(id int64, volume int) error {
	if volume < 1 || volume > 200 {
		return fmt.Errorf("volume must be between 1 and 200")
	}
	m.mu.Lock()
	defer m.mu.Unlock()
	s := m.state(id)
	old := s.Volume
	s.Volume = volume
	if err := m.persistLocked(); err != nil {
		s.Volume = old
		return err
	}
	return nil
}

func (m *Manager) ToggleShuffle(id int64) (bool, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	s := m.state(id)
	old := s.Shuffle
	s.Shuffle = !s.Shuffle
	if s.Shuffle {
		m.rng.Shuffle(len(s.Queue), func(i, j int) { s.Queue[i], s.Queue[j] = s.Queue[j], s.Queue[i] })
	}
	if err := m.persistLocked(); err != nil {
		s.Shuffle = old
		return false, err
	}
	return s.Shuffle, nil
}

func (m *Manager) Clear(id int64) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	old := m.chats[id]
	delete(m.chats, id)
	if err := m.persistLocked(); err != nil {
		if old != nil {
			m.chats[id] = old
		}
		return err
	}
	return nil
}
