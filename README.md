# 🎵 Mooze

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![Textual](https://img.shields.io/badge/UI-Textual-green)](https://textual.textualize.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

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

**Windows:**

```PowerShell
winget install ffmpeg
```

**MacOS:**

```PowerShell
brew install ffmpeg
```

**Linux:**

```PowerShell
sudo apt install ffmpeg
```

*(Note: Restart your terminal after installing FFmpeg so your system recognizes it.)*

---

## 🚀 Installation

Because Mooze is packaged professionally, you can install it globally on your system.

1. Clone the repository:

```Shell
git clone [https://github.com/X0fx/mooze.git](https://github.com/X0fx/mooze.git)
cd mooze
```

2. Install the application:

```Shell
pip install -e .
```

---

## 📖 User Manual

Once installed, simply type `mooze` in any terminal to launch the dashboard.

### 📥 Single Song Download

1. Ensure the **Batch Mode** switch is toggled  **OFF** .
2. In the input box, paste a **Spotify Track Link** (e.g., `https://open.spotify.com/track/...`) OR type a search term (e.g., `Mozart Requiem`).
3. Select your desired audio format from the dropdown menu.
4. Type your save folder path (e.g., `C:/Users/YourName/Downloads` or just `./` for the current folder).
5. Click  **Search & Download** .

### 📦 Batch Downloading

1. Toggle the **Batch Mode** switch to  **ON** . The UI will dynamically expand.
2. Paste multiple Spotify links into the text area. **You must put exactly one link per line.**
3. Select your audio format and your save location.
4. Click  **Download Batch** .

*Note: Mooze will create a temporary folder, process all your songs, compress them into a `Mooze_Batch_Archive.zip` file in your save directory, and clean up the temporary files automatically.*

---

## ⚠️ Disclaimer

This tool is for educational purposes and personal use only. It relies on publicly available APIs and YouTube search mechanisms. Please respect digital rights and support the artists you listen to.
