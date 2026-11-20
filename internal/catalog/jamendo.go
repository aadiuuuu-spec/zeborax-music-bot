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

type LicensedTrack struct {
	ID        string
	Title     string
	Artist    string
	StreamURL string
	License   string
}

type jamendoResponse struct {
	Headers struct {
		Status       string `json:"status"`
		ErrorMessage string `json:"error_message"`
	} `json:"headers"`
	Results []struct {
		ID         string `json:"id"`
		Name       string `json:"name"`
		ArtistName string `json:"artist_name"`
		Audio      string `json:"audio"`
		LicenseURL string `json:"license_ccurl"`
	} `json:"results"`
}

var jamendoHTTPClient = &http.Client{Timeout: 12 * time.Second}

// SearchLicensed returns full-length Jamendo streams only when their published
// Creative Commons license is in the conservative allow-list (CC0, CC BY,
// or CC BY-SA). It never uses the download URL.
func SearchLicensed(ctx context.Context, query, clientID string) ([]LicensedTrack, error) {
	query = strings.TrimSpace(query)
	clientID = strings.TrimSpace(clientID)
	if query == "" {
		return nil, errors.New("song name is empty")
	}
	if clientID == "" {
		return nil, errors.New("JAMENDO_CLIENT_ID is not configured")
	}

	values := url.Values{}
	values.Set("client_id", clientID)
	values.Set("format", "json")
	values.Set("limit", "15")
	values.Set("audioformat", "mp32")
	values.Set("include", "licenses")
	values.Set("search", query)
	endpoint := "https://api.jamendo.com/v3.0/tracks/?" + values.Encode()

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, endpoint, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("User-Agent", "ZeboraX-Music-Bot/1.0")
	resp, err := jamendoHTTPClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("Jamendo search failed: %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("Jamendo returned HTTP %d", resp.StatusCode)
	}

	var payload jamendoResponse
	if err := json.NewDecoder(io.LimitReader(resp.Body, 3<<20)).Decode(&payload); err != nil {
		return nil, fmt.Errorf("decode Jamendo response: %w", err)
	}
	if !strings.EqualFold(payload.Headers.Status, "success") {
		if payload.Headers.ErrorMessage != "" {
			return nil, fmt.Errorf("Jamendo: %s", payload.Headers.ErrorMessage)
		}
		return nil, errors.New("Jamendo search was not successful")
	}

	tracks := make([]LicensedTrack, 0, len(payload.Results))
	for _, item := range payload.Results {
		streamURL := strings.TrimSpace(item.Audio)
		licenseURL := strings.TrimSpace(item.LicenseURL)
		if strings.TrimSpace(item.Name) == "" || streamURL == "" || !allowedCreativeCommonsLicense(licenseURL) {
			continue
		}
		u, err := url.Parse(streamURL)
		if err != nil || (u.Scheme != "https" && u.Scheme != "http") || u.Host == "" {
			continue
		}
		tracks = append(tracks, LicensedTrack{
			ID: item.ID, Title: item.Name, Artist: item.ArtistName,
			StreamURL: streamURL, License: licenseURL,
		})
	}
	if len(tracks) == 0 {
		return nil, errors.New("no full-length result with an allowed CC0, CC BY, or CC BY-SA license was found")
	}
	return tracks, nil
}

func allowedCreativeCommonsLicense(raw string) bool {
	u, err := url.Parse(strings.TrimSpace(raw))
	if err != nil || !strings.EqualFold(u.Hostname(), "creativecommons.org") {
		return false
	}
	path := strings.Trim(strings.ToLower(u.Path), "/")
	parts := strings.Split(path, "/")
	if len(parts) < 3 {
		return false
	}
	if parts[0] == "publicdomain" && parts[1] == "zero" {
		return true
	}
	if parts[0] != "licenses" || len(parts) < 3 {
		return false
	}
	return parts[1] == "by" || parts[1] == "by-sa"
}
