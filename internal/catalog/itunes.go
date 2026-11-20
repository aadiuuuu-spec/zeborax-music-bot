package catalog

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"time"
)

type Track struct {
	Title      string
	Artist     string
	PreviewURL string
}

type searchResponse struct {
	Results []struct {
		TrackName  string `json:"trackName"`
		ArtistName string `json:"artistName"`
		PreviewURL string `json:"previewUrl"`
	} `json:"results"`
}

var httpClient = &http.Client{Timeout: 10 * time.Second}

// Search returns playable short previews from Apple's public iTunes Search API.
func Search(ctx context.Context, query string) ([]Track, error) {
	query = strings.TrimSpace(query)
	if query == "" {
		return nil, errors.New("song name is empty")
	}
	endpoint := "https://itunes.apple.com/search?term=" + url.QueryEscape(query) + "&entity=song&limit=8"
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, endpoint, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("User-Agent", "ZeboraX-Music-Bot/1.0")
	resp, err := httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("music search failed: %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("music search returned HTTP %d", resp.StatusCode)
	}
	var payload searchResponse
	if err := json.NewDecoder(io.LimitReader(resp.Body, 2<<20)).Decode(&payload); err != nil {
		return nil, fmt.Errorf("decode music search: %w", err)
	}
	tracks := make([]Track, 0, len(payload.Results))
	for _, item := range payload.Results {
		if strings.TrimSpace(item.TrackName) == "" || strings.TrimSpace(item.PreviewURL) == "" {
			continue
		}
		tracks = append(tracks, Track{
			Title: item.TrackName, Artist: item.ArtistName, PreviewURL: item.PreviewURL,
		})
	}
	if len(tracks) == 0 {
		return nil, errors.New("no playable preview found for that song")
	}
	return tracks, nil
}
