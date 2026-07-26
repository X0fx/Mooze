import yt_dlp
import urllib.request
import json
import re
import os
import shutil
import subprocess
from typing import Any

def get_ffmpeg_path():
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
        
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return None

def expand_if_playlist(url: str) -> list[str]:
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

def get_spotify_query(url: str) -> tuple[str, str | None]:
    """Extracts both the query (Title + Artist) and the Spotify Album Art URL."""
    clean_url = url.split('?')[0]
    thumbnail_url = None
    
    # 1. Prioritize OEmbed (Reliably provides title, artist, and high-res cover art)
    try:
        oembed_url = f"https://open.spotify.com/oembed?url={clean_url}"
        req = urllib.request.Request(oembed_url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req).read().decode('utf-8')
        data = json.loads(response)
        
        if "thumbnail_url" in data:
            thumbnail_url = data["thumbnail_url"]
            
        if "title" in data and "author_name" in data:
            return f"{data['title']} {data['author_name']}", thumbnail_url
        elif "title" in data:
            return data["title"], thumbnail_url
    except Exception:
        pass

    # 2. Fallback to HTML scraping
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
                return clean_title.strip(), thumbnail_url
    except Exception:
        pass 
        
    raise ValueError("Could not translate Spotify link. Try typing the song name instead!")

def download_song(search_query: str, save_location: str, format_choice: str, progress_callback=None) -> str:
    spotify_thumb = None
    
    # Check if we need to scrape Spotify metadata and artwork
    if "spotify.com" in search_query:
        search_query, spotify_thumb = get_spotify_query(search_query)

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

    postprocessors: list[dict[str, Any]] = [
        {'key': 'SponsorBlock', 'categories': ['music_offtopic', 'intro', 'outro', 'sponsor']},
        {'key': 'ModifyChapters', 'remove_sponsor_segments': ['music_offtopic', 'intro', 'outro', 'sponsor']},
        {'key': 'FFmpegExtractAudio', 'preferredcodec': codec, 'preferredquality': quality,}
    ]
    
    # Only let yt-dlp handle thumbnails if it's NOT a Spotify track
    ydl_embed_art = embed_art and not spotify_thumb
    
    if ydl_embed_art:
        postprocessors.append({'key': 'FFmpegThumbnailsConvertor', 'format': 'jpg'})
        postprocessors.append({'key': 'EmbedThumbnail'})
        
    postprocessors.append({'key': 'FFmpegMetadata', 'add_metadata': True})

    ffmpeg_path = get_ffmpeg_path()

    options: Any = {
        'format': 'bestaudio/best',
        'ffmpeg_location': ffmpeg_path,
        'outtmpl': f'{save_location}/%(title)s.%(ext)s',
        'default_search': 'ytsearch1:',
        'noplaylist': True,
        'writethumbnail': ydl_embed_art, 
        'progress_hooks': [my_hook], 
        'postprocessors': postprocessors,
        'concurrent_fragment_downloads': 5, 
        'http_chunk_size': 10485760,        
        'retries': 10,                      
        'fragment_retries': 10,             
        'file_access_retries': 5,           
        'postprocessor_args': {'ffmpeg': ['-threads', '0']}
    }
    
    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(search_query, download=True)
        if not info:
            raise ValueError("Could not extract media metadata.")
        raw_filepath = ydl.prepare_filename(info)
        base_path, _ = os.path.splitext(raw_filepath)
        final_file = f"{base_path}.{codec}"

    # --- SPOTIFY ARTWORK EMBEDDING ---
    if spotify_thumb and embed_art and ffmpeg_path:
        thumb_path = f"{base_path}_cover.jpg"
        temp_file = f"{base_path}_temp.{codec}"
        
        try:
            # 1. Download Spotify cover image
            req = urllib.request.Request(spotify_thumb, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response, open(thumb_path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
                
            # 2. Merge image and audio using FFmpeg
            if codec == "mp3":
                subprocess.run([ffmpeg_path, '-y', '-i', final_file, '-i', thumb_path, '-map', '0:0', '-map', '1:0', '-c', 'copy', '-id3v2_version', '3', '-metadata:s:v', 'title="Album cover"', '-metadata:s:v', 'comment="Cover (front)"', temp_file], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                shutil.move(temp_file, final_file)
            elif codec in ["m4a", "mp4"]:
                subprocess.run([ffmpeg_path, '-y', '-i', final_file, '-i', thumb_path, '-map', '0:0', '-map', '1:0', '-c', 'copy', '-disposition:v', 'attached_pic', temp_file], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                shutil.move(temp_file, final_file)
        except Exception:
            pass # Failsafe: If embedding fails, keep the valid audio file
        finally:
            if os.path.exists(thumb_path):
                os.remove(thumb_path)
            if os.path.exists(temp_file):
                os.remove(temp_file)

    return final_file