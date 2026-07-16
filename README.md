# 🎵 Mooze

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![Textual](https://img.shields.io/badge/UI-Textual-green)](https://textual.textualize.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Mooze is a sleek, responsive, terminal-based desktop application for downloading high-quality audio. It bypasses DRM to intelligently translate Spotify links and fetches the best available audio directly to your machine.

---

## ✨ Features

* **Dual Download Modes:**
  * **Single Mode:** Paste a Spotify track link or type a raw search query (e.g., "Coldplay Yellow").
  * **Batch Mode:** Paste a list of multiple Spotify links (one per line) to download them all at once. Batch downloads are automatically zipped into a neat archive!
* **Smart Spotify Translation:** Bypasses web-scrapers using oEmbed and Googlebot masking to accurately extract Track + Artist data.
* **Audiophile Quality:** Choose your preferred output:
  * MP3 - High Quality (320kbps)
  * MP3 - Normal (128kbps)
  * WAV - Best Quality (Lossless)
* **Modern Terminal UI:** Built with Textual, featuring mouse support, smooth toggle switches, and background asynchronous workers to keep the UI perfectly responsive while downloading.

---

## 🛠️ Prerequisites

Mooze uses `yt-dlp` under the hood, which requires **FFmpeg** to convert video files into clean MP3/WAV audio.

**Windows:** Open Command Prompt or PowerShell and run:

```bash
winget install ffmpeg
```

# Mooze 🎵

A sleek, responsive, terminal-based desktop application for downloading high-quality audio directly from Spotify links or text searches. Built with Python and the Textual TUI framework.

## ✨ Features

* **Single Song Download:** Search by song name or paste a direct Spotify link.
* **Batch Downloading:** Paste a list of multiple Spotify links (one per line) to download them all at once. Batch downloads are automatically packaged into a clean `.zip` archive!
* **High-Quality Audio:** Choose your preferred output format:
  * MP3 - High Quality (320kbps)
  * MP3 - Normal (128kbps)
  * WAV - Best Quality (Lossless)
* **Smart Spotify Translation:** Bypasses DRM by automatically translating Spotify links into the correct song/artist combinations using oEmbed and Googlebot masking.
* **Modern Terminal UI:** A beautiful, mouse-friendly, responsive dashboard with toggle switches, loading spinners, and progress notifications.

## 🛠️ Prerequisites

Before you run Mooze, you must have **FFmpeg** installed on your computer. This is the master audio converter the engine uses under the hood.

**Windows:**
Open Command Prompt and run:

```bash
winget install ffmpeg
```
