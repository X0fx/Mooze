import yt_dlp
import urllib.request
import json
import re
import os
from typing import Any

def expand_if_playlist(url: str) -> list[str]:
    """Scrapes a Spotify playlist or album URL to extract all track links natively."""
    if "spotify.com/playlist" in url or "spotify.com/album" in url:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            html = urllib.request.urlopen(req).read().decode('utf-8')
            track_ids = re.findall(r'href="https://open.spotify.com/track/([a-zA-Z0-9]+)"', html)
            
            seen = set()
            urls = []
            for tid in track_ids:
                if tid not in seen:
                    seen.add(tid)
                    urls.append(f"https://open.spotify.com/track/{tid}")
            return urls if urls else [url]
        except Exception:
            return [url]
    return [url]

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
            clean_title = raw_title.replace('| Spotify', '').replace('- song and lyrics by', ' ').replace('- song by', ' ').replace('- single by', ' ')
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

def download_song(search_query: str, save_location: str, format_choice: str, progress_callback=None) -> str:
    if "spotify.com" in search_query:
        search_query = get_spotify_query(search_query)

    codec = "mp3"
    quality = "192"
    embed_art = True 
    
    try:
        parts = format_choice.split(",")
        if len(parts) == 2:
            codec = parts[0].strip()[1:].lower()
            quality_str = ''.join(filter(str.isdigit, parts[1]))
            if quality_str:
                quality = quality_str
    except Exception:
        pass 

    if codec in ["wav", "flac", "opus", "ogg"]:
        embed_art = False 
        
    def my_hook(d):
        if d['status'] == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            if progress_callback and total > 0:
                progress_callback(downloaded, total)

    postprocessors: list[dict[str, Any]] = [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': codec,
        'preferredquality': quality,
    }]
    
    if embed_art:
        postprocessors.append({'key': 'FFmpegThumbnailsConvertor', 'format': 'jpg'})
        postprocessors.append({'key': 'EmbedThumbnail'})
        
    postprocessors.append({'key': 'FFmpegMetadata', 'add_metadata': True})

    options: Any = {
        'format': 'bestaudio/best',
        'outtmpl': f'{save_location}/%(title)s.%(ext)s',
        'default_search': 'ytsearch1:',
        'noplaylist': True,
        'writethumbnail': embed_art, 
        'progress_hooks': [my_hook], 
        'postprocessors': postprocessors,
    }
    
    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(search_query, download=True)
        if not info:
            raise ValueError("Could not extract media metadata.")
        raw_filepath = ydl.prepare_filename(info)
        base_path, _ = os.path.splitext(raw_filepath)
        # Return the exact final file path so the audio player can target it
        return f"{base_path}.{codec}"