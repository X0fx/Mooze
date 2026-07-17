from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Button, TextArea, Label, ProgressBar, TabbedContent, TabPane, Collapsible
from textual.containers import Horizontal, Vertical
from textual import on, work, events
from textual.binding import Binding
from .downloader import download_song 
import os
import shutil
import json
import sys
import subprocess

CONFIG_FILE = os.path.expanduser("~/.mooze_settings.json")

class StaticHeader(Header):
    def on_click(self, event: events.Click):
        event.stop()
        event.prevent_default()

def load_settings():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_settings(format_choice, save_location, theme_choice):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({
                "format": format_choice, 
                "save_location": save_location,
                "theme": theme_choice
            }, f)
    except Exception:
        pass

class MoozeApp(App):
    TITLE = "Mooze"
    COMMAND_PALETTE_BINDING = ""

    CSS = """
    #main-area { height: 1fr; margin: 1; }
    
    /* FIXED: Changed from 1fr to auto so it hugs the search inputs tightly */
    #tabs { height: auto; }
    #single-tab, #batch-tab { padding: 1 2; height: auto; }
    
    #single-search-input { margin-bottom: 1; }
    
    #batch-label { margin-bottom: 1; color: $text-muted; }
    #batch-search-input { height: auto; min-height: 3; max-height: 12; }
    
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
        
        with Vertical(id="main-area"):
            with TabbedContent(id="tabs"):
                with TabPane("Single Download", id="single-tab"):
                    yield Input(placeholder="Paste a Spotify link or search for a song here...", id="single-search-input")
                    
                with TabPane("Batch Download", id="batch-tab"):
                    yield Label("Paste your list of Spotify links (One per line):", id="batch-label")
                    yield TextArea(id="batch-search-input")
            
            with Collapsible(title="Download Settings (Format & Save Path)", id="download-settings"):
                with Horizontal(id="options-row"):
                    yield Input(placeholder="Format (e.g. .flac, 192)", id="format-input")
                    yield Input(placeholder="Save Path (e.g. C:/Music)", id="save-location")
            
            yield Button("Start Download", variant="success", id="download-btn", classes="download-btn")
            yield ProgressBar(id="my-progress-bar")
        
        yield Footer()

    def on_mount(self):
        settings = load_settings()
        
        if "theme" in settings and settings["theme"]:
            self.theme = str(settings["theme"])
        else:
            self.theme = "textual-dark"
            
        if "format" in settings and settings["format"]:
            self.query_one("#format-input", Input).value = settings["format"]
            
        if "save_location" in settings and settings["save_location"]:
            self.query_one("#save-location", Input).value = settings["save_location"]

    @on(events.MouseDown)
    def handle_background_click(self, event: events.MouseDown):
        widget, _ = self.screen.get_widget_at(event.screen_x, event.screen_y)
        if widget and widget.id in ("main-area", "options-row", "single-tab", "batch-tab", "download-settings"):
            self.set_focus(None)

    def action_remove_focus(self):
        self.set_focus(None)
        
    def action_toggle_footer(self):
        footer = self.query_one(Footer)
        footer.display = not footer.display

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
    def action_theme_solarized_dark(self): self._apply_and_save_theme("solarized-dark")
    def action_theme_solarized_light(self): self._apply_and_save_theme("solarized-light")
    def action_theme_dracula(self): self._apply_and_save_theme("dracula")
    def action_theme_nord(self): self._apply_and_save_theme("nord")
    def action_theme_monokai(self): self._apply_and_save_theme("monokai")

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

    # =========================================================================
    # DOWNLOAD LOGIC & STRICT VALIDATION
    # =========================================================================

    @on(Button.Pressed)
    def start_downloading(self, event: Button.Pressed):
        if event.button.id != "download-btn":
            return
            
        format_input = self.query_one("#format-input", Input)
        save_location = self.query_one("#save-location", Input)
        single_input = self.query_one("#single-search-input", Input)
        batch_input = self.query_one("#batch-search-input", TextArea)
        
        format_input.remove_class("error")
        save_location.remove_class("error")
        single_input.remove_class("error")
        batch_input.remove_class("error")
        
        has_error = False
        
        raw_format = format_input.value.strip()
        is_valid_format = False
        
        if raw_format.startswith(".") and "," in raw_format:
            parts = raw_format.split(",")
            ext = parts[0].strip()[1:] 
            try:
                bitrate_str = ''.join(filter(str.isdigit, parts[1]))
                bitrate = int(bitrate_str) if bitrate_str else 0
                
                if 92 <= bitrate <= 320 and ext.isalnum():
                    is_valid_format = True
                    format_input.value = f".{ext.lower()}, {bitrate}"
            except ValueError:
                pass

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
            if is_valid_format: 
                self.notify("Oops! Please fill out all required fields.", severity="error")
            return
            
        save_settings(format_input.value, save_location.value, self.theme)
            
        progress_bar = self.query_one("#my-progress-bar", ProgressBar)
        progress_bar.display = True
        progress_bar.update(total=100, progress=0)
        
        self.notify("Starting your download process! Please wait...")
        self.run_engine(songs_to_download, save_location.value, format_input.value, is_batch_mode)

    def update_progress_ui(self, downloaded, total):
        progress_bar = self.query_one("#my-progress-bar", ProgressBar)
        progress_bar.update(total=total, progress=downloaded)

    @work(thread=True)
    def run_engine(self, songs, save_path, audio_format, is_batch):
        try:
            def progress_callback(downloaded, total):
                self.app.call_from_thread(self.update_progress_ui, downloaded, total)

            if is_batch and len(songs) > 1:
                working_path = os.path.join(save_path, "Mooze_Temp_Batch")
                os.makedirs(working_path, exist_ok=True)
            else:
                working_path = save_path

            for song in songs:
                if song.strip(): 
                    self.app.call_from_thread(self.update_progress_ui, 0, 100)
                    download_song(song.strip(), working_path, audio_format, progress_callback)
            
            if is_batch and len(songs) > 1:
                zip_filename = os.path.join(save_path, "Mooze_Batch_Archive")
                shutil.make_archive(zip_filename, 'zip', working_path)
                shutil.rmtree(working_path) 
                
            self.app.call_from_thread(self.finish_download, True, "All downloads completed successfully!")
        except Exception as e:
            self.app.call_from_thread(self.finish_download, False, str(e))
            
    def finish_download(self, success: bool, message: str):
        progress_bar = self.query_one("#my-progress-bar", ProgressBar)
        progress_bar.display = False
        if success:
            self.notify(message, title="Success!")
        else:
            self.notify(f"Engine Error: {message}", title="Oops!", severity="error")

    # =========================================================================
    # DPI-AWARE SCREENSHOT TOOL
    # =========================================================================
    def action_save_png(self):
        try:
            from PIL import ImageGrab
            import sys
            
            self.notify("Capturing screenshot...", title="Processing")
            filename = "mooze_screenshot.png"
            
            if sys.platform == "win32":
                import ctypes
                from ctypes import wintypes
                
                user32 = ctypes.windll.user32
                user32.SetProcessDPIAware()
                
                hwnd = user32.GetForegroundWindow()
                rect = wintypes.RECT()
                user32.GetWindowRect(hwnd, ctypes.byref(rect))
                
                bbox = (rect.left, rect.top, rect.right, rect.bottom)
                screenshot = ImageGrab.grab(bbox=bbox)
            else:
                screenshot = ImageGrab.grab()
                
            screenshot.save(filename)
            self.notify(f"Saved: {filename}", title="Screenshot", severity="information")
            
        except ImportError:
            self.notify("Missing dependency! Run: pip install pillow", severity="error", timeout=10)
        except Exception as e:
            self.notify(f"Screenshot failed: {str(e)}", title="Error", severity="error", timeout=15)

def start():
    app = MoozeApp()
    app.run()

if __name__ == "__main__":
    start()