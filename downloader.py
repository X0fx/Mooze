import yt_dlp
import urllib.request
import json
import re
from typing import Any

def get_spotify_query(url: str) -> str:
    """Uses a Googlebot disguise to extract both the song title AND the artist."""
    clean_url = url.split('?')[0]
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
        }
        req = urllib.request.Request(clean_url, headers=headers)
        html = urllib.request.urlopen(req).read().decode('utf-8')
        
        title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
        if title_match:
            raw_title = title_match.group(1)
            
            clean_title = raw_title.replace('| Spotify', '')
            clean_title = clean_title.replace('- song and lyrics by', ' ')
            clean_title = clean_title.replace('- song by', ' ')
            clean_title = clean_title.replace('- single by', ' ')
            
            if clean_title.strip():
                return clean_title.strip()
    except Exception:
        pass 
        
    try:
        oembed_url = f"https://open.spotify.com/oembed?url={clean_url}"
        req = urllib.request.Request(oembed_url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req).read().decode('utf-8')
        data = json.loads(response)
        
        if "title" in data and "author_name" in data:
            return f"{data['title']} {data['author_name']}"
        elif "title" in data:
            return data["title"]
    except Exception:
        pass
        
    raise ValueError("Could not translate Spotify link. Try typing the song name instead!")

def download_song(search_query: str, save_location: str, format_choice: str):
    
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
        
        # NEW: Tell the engine to download the album art/thumbnail!
        'writethumbnail': True, 
        
        'postprocessors': [
            # 1. Convert the audio to MP3/WAV
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': codec,
                'preferredquality': quality,
            },
            # NEW 2. Embed the downloaded thumbnail into the audio file as cover art
            {
                'key': 'EmbedThumbnail',
            },
            # NEW 3. Write the Artist, Title, and Date tags into the file's metadata
            {
                'key': 'FFmpegMetadata',
                'add_metadata': True,
            }
        ],
    }
    
    with yt_dlp.YoutubeDL(options) as ydl:
        ydl.download([search_query])