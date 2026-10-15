import urllib.request
import urllib.parse
import re

def get_spotify_track_uri(query: str):
    """Searches DuckDuckGo HTML for a Spotify track URL and converts to URI."""
    try:
        url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(f"site:open.spotify.com/track {query}")
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        html = urllib.request.urlopen(req, timeout=5).read().decode('utf-8')
        
        # Look for open.spotify.com/track/ID
        match = re.search(r'open\.spotify\.com/track/([a-zA-Z0-9]+)', html)
        if match:
            track_id = match.group(1)
            return f"spotify:track:{track_id}"
    except Exception as e:
        print("Error:", e)
        pass
    return None

if __name__ == "__main__":
    print(get_spotify_track_uri("shape of you ed sheeran"))
