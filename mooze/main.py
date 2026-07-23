from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Button, TextArea, Label, ProgressBar, TabbedContent, TabPane, Collapsible
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual import on, work, events
from textual.binding import Binding
from .downloader import download_song, expand_if_playlist 
import os
import shutil
import json
import sys
import subprocess
import datetime

CONFIG_FILE = os.path.expanduser("~/.mooze_settings.json")
HISTORY_FILE = os.path.expanduser("~/.mooze_history.json")

# Safely wrap the audio engine and ignore strict IDE type-checking warnings
try:
    import pygame  # type: ignore
    pygame.mixer.init()
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False

class StaticHeader(Header):
    def on_click(self, event: events.Click):
        event.stop()
        event.prevent_default()

def load_settings():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f: return json.load(f)
        except Exception: pass
    return {}

def save_settings(format_choice, save_location, theme_choice):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({"format": format_choice, "save_location": save_location, "theme": theme_choice}, f)
    except Exception: pass

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f: return json.load(f)
        except Exception: pass
    return []

def log_history(title, path):
    history = load_history()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    history.insert(0, {"title": title, "path": path, "time": timestamp})
    try:
        with open(HISTORY_FILE, "w") as f: json.dump(history[:50], f)
    except Exception: pass

class MoozeApp(App):
    TITLE = "Mooze"
    COMMAND_PALETTE_BINDING = ""

    CSS = """
    #workspace { layout: horizontal; height: 1fr; }
    #main-area { height: 1fr; margin: 1; width: 1fr; }
    
    #tabs { height: auto; }
    #single-tab, #batch-tab, #history-tab { padding: 1 2; height: auto; }
    #single-search-input { margin-bottom: 1; }
    #batch-label { margin-bottom: 1; color: $text-muted; }
    #batch-search-input { height: auto; min-height: 3; max-height: 12; }
    
    /* Queue Sidebar */
    #queue-sidebar { width: 35; dock: right; height: 1fr; border-left: tall $panel; padding: 0 1; display: none; }
    .queue-title { text-style: bold; color: $success; margin-bottom: 1; border-bottom: solid $panel; width: 100%; }
    #queue-list Label { width: 100%; padding: 0 1; }
    .queue-active { background: $accent; color: $text; }
    .queue-done { color: $success; }
    .queue-error { color: $error; }
    
    /* Audio Player Bar */
    #player-bar { dock: bottom; height: auto; padding: 1; border-top: tall $panel; align: left middle; }
    #player-bar Button { margin-right: 1; min-width: 10; }
    #player-status { color: $text-muted; margin-left: 1; }
    
    /* History List */
    #history-list { height: 12; border: solid $panel; margin-top: 1; }
    #history-list Label { padding: 0 1; }
    
    #download-settings { margin-top: 1; height: auto; }
    #options-row { height: auto; align: left middle; padding-top: 1; }
    #options-row Input { width: 1fr; margin: 0 1; }
    
    .download-btn { width: 100%; margin-top: 1; }
    #my-progress-bar { height: auto; margin: 1 2; display: none; }
    #options-row Input.error, #single-search-input.error, #batch-search-input.error { border: tall red; }
    """

    BINDINGS = [
        Binding("d", "quit", "Quit Mooze"),
        Binding("s", "save_png", "Screenshot (.png)"),
        Binding("k", "toggle_footer", "Toggle Keys Help"),
        Binding("escape", "remove_focus", "Deselect", show=False),
        Binding("alt+p", "command_palette", "Palette", show=False),
        Binding("ctrl+p", "command_palette", "Palette", show=False),
        Binding("backslash", "command_palette", "Palette", show=False),
    ]

    def compose(self) -> ComposeResult:
        yield StaticHeader(show_clock=False)
        
        with Horizontal(id="workspace"):
            with Vertical(id="main-area"):
                with TabbedContent(id="tabs"):
                    with TabPane("Single Download", id="single-tab"):
                        yield Input(placeholder="Paste a Spotify link or search for a song here...", id="single-search-input")
                        
                    with TabPane("Batch Download", id="batch-tab"):
                        yield Label("Paste your list of Spotify links (One per line):", id="batch-label")
                        yield TextArea(id="batch-search-input")
                        
                    with TabPane("History", id="history-tab"):
                        yield Button("↻ Refresh History", id="btn-refresh-history")
                        yield VerticalScroll(id="history-list")
                
                with Collapsible(title="Download Settings (Format & Save Path)", id="download-settings"):
                    with Horizontal(id="options-row"):
                        yield Input(placeholder="Format (e.g. .flac, 192)", id="format-input")
                        yield Input(placeholder="Save Path (e.g. C:/Music)", id="save-location")
                
                yield Button("Start Download", variant="success", id="download-btn", classes="download-btn")
                yield ProgressBar(id="my-progress-bar")
                
            with Vertical(id="queue-sidebar"):
                yield Label("Live Queue", classes="queue-title")
                yield VerticalScroll(id="queue-list")

        with Horizontal(id="player-bar"):
            yield Button("▶ Play", id="btn-play", disabled=True, variant="primary")
            yield Button("⏹ Stop", id="btn-stop", disabled=True, variant="error")
            yield Label("Player Ready (Requires pygame)", id="player-status")
            
        yield Footer()

    def on_mount(self):
        settings = load_settings()
        self.theme = settings.get("theme", "textual-dark")
        self.query_one("#format-input", Input).value = settings.get("format", ".mp3, 320")
        self.query_one("#save-location", Input).value = settings.get("save_location", "")
        
        self.last_downloaded_path = None
        self.refresh_history_ui()
        self.check_updates()

    # Helper method to safely toggle progress bar visibility from background threads
    def set_progress_bar_visible(self, visible: bool):
        self.query_one("#my-progress-bar", ProgressBar).display = visible

    @work(thread=True)
    def check_updates(self):
        try:
            import urllib.request
            req = urllib.request.Request("https://pypi.org/pypi/mooze-dl/json", headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib.request.urlopen(req, timeout=3).read().decode('utf-8')
            latest = json.loads(response)["info"]["version"]
            if latest != "1.0.0":
                self.app.call_from_thread(self.notify, f"Update v{latest} available! Run: pip install -U mooze-dl", title="Update", timeout=15)
        except Exception:
            pass

    def refresh_history_ui(self):
        container = self.query_one("#history-list")
        container.remove_children()
        history = load_history()
        for item in history:
            container.mount(Label(f"[{item.get('time')}] {item.get('title')[:50]}"))

    @on(events.MouseDown)
    def handle_background_click(self, event: events.MouseDown):
        widget, _ = self.screen.get_widget_at(event.screen_x, event.screen_y)
        if widget and widget.id in ("main-area", "options-row", "single-tab", "batch-tab", "download-settings", "workspace"):
            self.set_focus(None)

    def action_remove_focus(self): self.set_focus(None)
    def action_toggle_footer(self): self.query_one(Footer).display = not self.query_one(Footer).display

    @on(Button.Pressed)
    def handle_buttons(self, event: Button.Pressed):
        btn_id = event.button.id
        
        if btn_id == "btn-refresh-history":
            self.refresh_history_ui()
            self.notify("History refreshed.")
            
        elif btn_id == "btn-play":
            if not HAS_PYGAME:
                self.notify("Please install the audio engine: pip install pygame", severity="error")
                return
            if self.last_downloaded_path and os.path.exists(self.last_downloaded_path):
                try:
                    pygame.mixer.music.load(self.last_downloaded_path)
                    pygame.mixer.music.play()
                    self.query_one("#player-status", Label).update(f"🔊 Playing: {os.path.basename(self.last_downloaded_path)}")
                except Exception as e:
                    self.notify(f"Playback error: {e}", severity="error")
                    
        elif btn_id == "btn-stop":
            if HAS_PYGAME:
                pygame.mixer.music.stop()
                self.query_one("#player-status", Label).update("⏹ Stopped")
                
        elif btn_id == "download-btn":
            self.initiate_download_validation()

    def initiate_download_validation(self):
        format_input = self.query_one("#format-input", Input)
        save_location = self.query_one("#save-location", Input)
        single_input = self.query_one("#single-search-input", Input)
        batch_input = self.query_one("#batch-search-input", TextArea)
        
        format_input.remove_class("error")
        save_location.remove_class("error")
        single_input.remove_class("error")
        batch_input.remove_class("error")
        
        has_error, is_valid_format = False, False
        raw_format = format_input.value.strip()
        
        if raw_format.startswith(".") and "," in raw_format:
            parts = raw_format.split(",")
            ext = parts[0].strip()[1:] 
            try:
                bitrate_str = ''.join(filter(str.isdigit, parts[1]))
                bitrate = int(bitrate_str) if bitrate_str else 0
                if 92 <= bitrate <= 320 and ext.isalnum():
                    is_valid_format = True
                    format_input.value = f".{ext.lower()}, {bitrate}"
            except ValueError: pass

        if not is_valid_format:
            format_input.add_class("error")
            has_error = True
            self.notify("Format must be '.ext, bitrate' (e.g. .mp3, 320). Bitrate limit: 92-320.", severity="error", timeout=6)
            self.query_one("#download-settings", Collapsible).collapsed = False
            
        if save_location.value.strip() == "":
            save_location.add_class("error")
            has_error = True
            self.query_one("#download-settings", Collapsible).collapsed = False
            
        active_tab = self.query_one("#tabs", TabbedContent).active
        is_batch_mode = (active_tab == "batch-tab")
        
        if is_batch_mode:
            raw_text = batch_input.text
            if not raw_text.strip():
                batch_input.add_class("error")
                has_error = True
            songs_to_download = raw_text.strip().split("\n")
        else:
            raw_text = single_input.value
            if not raw_text.strip():
                single_input.add_class("error")
                has_error = True
            songs_to_download = [raw_text.strip()]
            
        if has_error:
            if is_valid_format: self.notify("Oops! Please fill out all required fields.", severity="error")
            return
            
        save_settings(format_input.value, save_location.value, self.theme)
        self.set_progress_bar_visible(True)
        self.query_one("#my-progress-bar", ProgressBar).update(total=100, progress=0)
        self.notify("Initializing worker engine...")
        
        self.run_engine(songs_to_download, save_location.value, format_input.value, is_batch_mode)

    def init_queue_ui(self, songs):
        self.query_one("#queue-sidebar").display = True
        q_list = self.query_one("#queue-list")
        q_list.remove_children()
        for idx, s in enumerate(songs):
            display_name = s[:30] + "..." if len(s) > 30 else s
            lbl = Label(f"⏳ {display_name}", id=f"q-item-{idx}")
            setattr(lbl, "song_name", display_name)
            q_list.mount(lbl)

    def update_queue_ui(self, index, state):
        try:
            lbl = self.query_one(f"#q-item-{index}", Label)
            name = getattr(lbl, "song_name", "Song")
            if state == "active":
                lbl.update(f"▶ {name}")
                lbl.add_class("queue-active")
            elif state == "done":
                lbl.update(f"✅ {name}")
                lbl.remove_class("queue-active")
                lbl.add_class("queue-done")
            elif state == "error":
                lbl.update(f"❌ {name}")
                lbl.remove_class("queue-active")
                lbl.add_class("queue-error")
        except Exception: pass

    def enable_player(self):
        self.query_one("#btn-play", Button).disabled = False
        self.query_one("#btn-stop", Button).disabled = False
        if self.last_downloaded_path:
            self.query_one("#player-status", Label).update(f"Ready: {os.path.basename(self.last_downloaded_path)}")

    @work(thread=True)
    def run_engine(self, songs, save_path, audio_format, is_batch):
        try:
            expanded_songs = []
            for song in songs:
                if song.strip():
                    expanded_songs.extend(expand_if_playlist(song.strip()))
            
            self.app.call_from_thread(self.init_queue_ui, expanded_songs)

            if is_batch and len(expanded_songs) > 1:
                working_path = os.path.join(save_path, "Mooze_Temp_Batch")
                os.makedirs(working_path, exist_ok=True)
            else:
                working_path = save_path

            for idx, song in enumerate(expanded_songs):
                self.app.call_from_thread(self.update_queue_ui, idx, "active")
                self.app.call_from_thread(self.query_one("#my-progress-bar", ProgressBar).update, total=100, progress=0)
                
                try:
                    final_path = download_song(song, working_path, audio_format, lambda d, t: self.app.call_from_thread(self.query_one("#my-progress-bar", ProgressBar).update, total=t, progress=d))
                    log_history(song, final_path)
                    self.last_downloaded_path = final_path
                    self.app.call_from_thread(self.update_queue_ui, idx, "done")
                except Exception as e:
                    self.app.call_from_thread(self.update_queue_ui, idx, "error")
                    self.app.call_from_thread(self.notify, f"Error: {e}", severity="error")
            
            if is_batch and len(expanded_songs) > 1:
                zip_filename = os.path.join(save_path, "Mooze_Batch_Archive")
                shutil.make_archive(zip_filename, 'zip', working_path)
                shutil.rmtree(working_path) 
                
            self.app.call_from_thread(self.enable_player)
            self.app.call_from_thread(self.set_progress_bar_visible, False)
            self.app.call_from_thread(self.notify, "All downloads completed successfully!", title="Success")
        except Exception as e:
            self.app.call_from_thread(self.set_progress_bar_visible, False)
            self.app.call_from_thread(self.notify, f"Engine Error: {str(e)}", title="Oops!", severity="error")

    # =========================================================================
    # COMMAND PALETTE
    # =========================================================================
    def _apply_and_save_theme(self, theme_name: str):
        self.theme = theme_name
        fmt = self.query_one("#format-input", Input).value
        loc = self.query_one("#save-location", Input).value
        save_settings(fmt, loc, theme_name)
        self.notify(f"Theme updated to {theme_name}", severity="information")

    def action_theme_dark(self): self._apply_and_save_theme("textual-dark")
    def action_theme_light(self): self._apply_and_save_theme("textual-light")
    def action_theme_dracula(self): self._apply_and_save_theme("dracula")
    def action_theme_nord(self): self._apply_and_save_theme("nord")

    def action_clear_inputs(self):
        self.query_one("#single-search-input", Input).value = ""
        self.query_one("#batch-search-input", TextArea).text = ""
        self.notify("All inputs cleared.", severity="information")

    def action_open_download_folder(self):
        path = self.query_one("#save-location", Input).value
        if not path or not os.path.exists(path):
            self.notify("The save folder does not exist yet!", severity="error")
            return
        try:
            if sys.platform == "win32": os.startfile(path)
            elif sys.platform == "darwin": subprocess.call(["open", path])
            else: subprocess.call(["xdg-open", path])
        except Exception as e:
            self.notify(f"Could not open folder: {e}", severity="error")

    def action_save_png(self):
        try:
            from PIL import ImageGrab
            
            if sys.platform == "win32":
                import ctypes
                from ctypes import wintypes
                ctypes.windll.user32.SetProcessDPIAware() 
                hwnd = ctypes.windll.user32.GetForegroundWindow()
                rect = wintypes.RECT()
                ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
                bbox = (rect.left, rect.top, rect.right, rect.bottom)
                ImageGrab.grab(bbox=bbox).save("mooze_screenshot.png")
            else:
                ImageGrab.grab().save("mooze_screenshot.png")
                
            self.notify("Saved mooze_screenshot.png", severity="information")
        except Exception as e: 
            self.notify(str(e), severity="error")

def start(): MoozeApp().run()
if __name__ == "__main__": start()