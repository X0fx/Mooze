import yt_dlp
import urllib.request
import json
import re
from typing import Any

def get_spotify_query(url: str) -> str:
    """Uses a Googlebot disguise to extract both the song title AND the artist."""
    clean_url = url.split('?')[0]
    
    # Method 1: The Googlebot Disguise (Highly accurate, gets Title + Artist)
    try:
        # We tell Spotify we are Google's search engine bot!
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
        }
        req = urllib.request.Request(clean_url, headers=headers)
        html = urllib.request.urlopen(req).read().decode('utf-8')
        
        # Look for the hidden title tag
        title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
        if title_match:
            raw_title = title_match.group(1)
            
            # Spotify formats it as: "Song - song and lyrics by Artist | Spotify"
            clean_title = raw_title.replace('| Spotify', '')
            clean_title = clean_title.replace('- song and lyrics by', ' ')
            clean_title = clean_title.replace('- song by', ' ')
            clean_title = clean_title.replace('- single by', ' ')
            
            if clean_title.strip():
                return clean_title.strip() # We successfully return "Song Artist"
    except Exception:
        pass # If Googlebot fails, move to the backup plan
        
    # Method 2: The Backup oEmbed Plan (If the site blocks us completely)
    try:
        oembed_url = f"https://open.spotify.com/oembed?url={clean_url}"
        req = urllib.request.Request(oembed_url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req).read().decode('utf-8')
        data = json.loads(response)
        
        # If the backup gives us an author, combine them!
        if "title" in data and "author_name" in data:
            return f"{data['title']} {data['author_name']}"
        elif "title" in data:
            return data["title"]
    except Exception:
        pass
        
    raise ValueError("Could not translate Spotify link. Try typing the song name instead!")

def download_song(search_query: str, save_location: str, format_choice: str):
    
    # Check if we need to translate a Spotify link
    if "spotify.com" in search_query:
        search_query = get_spotify_query(search_query)

    codec = "mp3"
    quality = "192" 
    
    if format_choice == "mp3_high":
        codec = "mp3"
        quality = "320"
    elif format_choice == "mp3_normal":
        codec = "mp3"
        quality = "128"
    elif format_choice == "wav":
        codec = "wav"
        quality = "192"

    options: Any = {
        'format': 'bestaudio/best',
        'outtmpl': f'{save_location}/%(title)s.%(ext)s',
        'default_search': 'ytsearch1:',
        'noplaylist': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': codec,
            'preferredquality': quality,
        }],
    }
    
    with yt_dlp.YoutubeDL(options) as ydl:
        ydl.download([search_query])