package catalog

import "testing"

func TestAllowedCreativeCommonsLicense(t *testing.T) {
	tests := []struct {
		url string
		want bool
	}{
		{"https://creativecommons.org/licenses/by/4.0/", true},
		{"https://creativecommons.org/licenses/by-sa/4.0/", true},
		{"https://creativecommons.org/publicdomain/zero/1.0/", true},
		{"https://creativecommons.org/licenses/by-nc/4.0/", false},
		{"https://creativecommons.org/licenses/by-nd/4.0/", false},
		{"https://creativecommons.org/licenses/by-nc-sa/4.0/", false},
		{"https://example.com/licenses/by/4.0/", false},
		{"", false},
	}
	for _, tc := range tests {
		if got := allowedCreativeCommonsLicense(tc.url); got != tc.want {
			t.Errorf("allowedCreativeCommonsLicense(%q) = %v, want %v", tc.url, got, tc.want)
		}
	}
}
