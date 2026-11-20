package music

import (
	"errors"
	"path/filepath"
	"testing"
)

func TestQueuePersistsAndIsIsolated(t *testing.T) {
	path := filepath.Join(t.TempDir(), "state", "queue.json")
	m, err := New(path)
	if err != nil { t.Fatal(err) }
	if _, err := m.Add(-1001, "  song one  ", "tester"); err != nil { t.Fatal(err) }
	if _, err := m.Add(-1002, "song two", "tester"); err != nil { t.Fatal(err) }

	reloaded, err := New(path)
	if err != nil { t.Fatal(err) }
	a := reloaded.Snapshot(-1001)
	b := reloaded.Snapshot(-1002)
	if len(a.Queue) != 1 || a.Queue[0].Query != "song one" { t.Fatalf("unexpected first queue: %#v", a) }
	if len(b.Queue) != 1 || b.Queue[0].Query != "song two" { t.Fatalf("unexpected second queue: %#v", b) }
}

func TestRejectsEmptyQuery(t *testing.T) {
	m, _ := New("")
	_, err := m.Add(1, "   ", "")
	if !errors.Is(err, ErrEmptyQuery) { t.Fatalf("expected ErrEmptyQuery, got %v", err) }
}

func TestVolumeBounds(t *testing.T) {
	m, _ := New("")
	if err := m.SetVolume(1, 201); err == nil { t.Fatal("expected out-of-range volume error") }
	if err := m.SetVolume(1, 75); err != nil { t.Fatal(err) }
}
