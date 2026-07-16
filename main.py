from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Button, Select, TextArea, Switch, Label, LoadingIndicator
from textual.containers import Horizontal, Vertical
from textual import on, work 
from downloader import download_song 
import os
import shutil

class MoozeApp(App):
    CSS = """
    #main-area { height: 1fr; }
    #toggle-row { height: auto; margin: 1; align: left middle; }
    #toggle-row Label { margin-right: 1; padding-top: 1; }
    #single-mode { height: auto; margin: 1; }
    #single-mode Input { width: 1fr; }
    
    /* NEW: Batch mode and TextArea now flex intelligently instead of acting like bullies! */
    #batch-mode { height: 1fr; margin: 1; display: none; }
    TextArea { height: 1fr; }
    #batch-controls { align: right middle; padding-right: 2; height: auto; margin-top: 1; }
    
    /* NEW: We force the spinner to be exactly 1 line tall so it never gets crushed */
    #my-progress-bar { height: 1; margin: 1 2; display: none; }
    
    #options-row { dock: bottom; height: auto; align: left middle; margin: 1; }
    #options-row Select, #options-row Input { width: 1fr; margin: 0 1; }
    #options-row Select { border: tall transparent; }
    #options-row Select.error, #options-row Input.error { border: tall red; }
    """

    BINDINGS = [("d", "quit", "Quit Mooze")]

    def compose(self) -> ComposeResult:
        yield Header()
        
        with Vertical(id="main-area"):
            with Horizontal(id="toggle-row"):
                yield Label("Batch Mode:")
                yield Switch(id="batch-switch")
            
            with Horizontal(id="single-mode"):
                yield Input(placeholder="Paste a Spotify link or search for a song here...", id="single-search-input")
                yield Button("Search & Download", variant="success")
                
            with Vertical(id="batch-mode"):
                yield Label("Paste your list of Spotify links below (One per line):")
                yield TextArea(id="batch-search-input")
                with Horizontal(id="batch-controls"):
                    yield Button("Download Batch", variant="success")
            
            yield LoadingIndicator(id="my-progress-bar")
        
        with Horizontal(id="options-row"):
            yield Select(
                options=[
                    ("MP3 - High Quality (320kbps)", "mp3_high"),
                    ("MP3 - Normal (128kbps)", "mp3_normal"),
                    ("WAV - Best Quality (Lossless)", "wav")
                ],
                prompt="Choose Format & Quality...",
                id="format-select"
            )
            yield Input(placeholder="Where to save? (e.g., Desktop or C:/Music)", id="save-location")
        
        yield Footer()

    @on(Switch.Changed)
    def toggle_views(self, event: Switch.Changed):
        single_view = self.query_one("#single-mode")
        batch_view = self.query_one("#batch-mode")
        
        if event.value:
            single_view.display = False
            batch_view.display = True
        else:
            single_view.display = True
            batch_view.display = False

    @on(Button.Pressed)
    def start_downloading(self):
        format_select = self.query_one("#format-select", Select)
        save_location = self.query_one("#save-location", Input)
        
        format_select.remove_class("error")
        save_location.remove_class("error")
        
        has_error = False
        
        if format_select.value == Select.BLANK:
            format_select.add_class("error")
            has_error = True
            
        if save_location.value.strip() == "":
            save_location.add_class("error")
            has_error = True
            
        if has_error:
            self.notify("Oops! Please choose a format and a save location.", severity="error")
            return
            
        batch_switch = self.query_one("#batch-switch", Switch)
        is_batch_mode = batch_switch.value
        
        if is_batch_mode:
            raw_text = self.query_one("#batch-search-input", TextArea).text
            songs_to_download = raw_text.strip().split("\n")
        else:
            raw_text = self.query_one("#single-search-input", Input).value
            songs_to_download = [raw_text.strip()]
            
        loading_spinner = self.query_one("#my-progress-bar", LoadingIndicator)
        loading_spinner.display = True
        
        self.notify("Starting your download process! Please wait...")
        self.run_engine(songs_to_download, save_location.value, format_select.value, is_batch_mode)

    @work(thread=True)
    def run_engine(self, songs, save_path, audio_format, is_batch):
        try:
            if is_batch and len(songs) > 1:
                working_path = os.path.join(save_path, "Mooze_Temp_Batch")
                os.makedirs(working_path, exist_ok=True)
            else:
                working_path = save_path

            for song in songs:
                if song.strip(): 
                    download_song(song.strip(), working_path, audio_format)
            
            if is_batch and len(songs) > 1:
                zip_filename = os.path.join(save_path, "Mooze_Batch_Archive")
                shutil.make_archive(zip_filename, 'zip', working_path)
                shutil.rmtree(working_path) 
                
            self.app.call_from_thread(self.finish_download, True, "All downloads completed successfully!")
        except Exception as e:
            self.app.call_from_thread(self.finish_download, False, str(e))
            
    def finish_download(self, success: bool, message: str):
        loading_spinner = self.query_one("#my-progress-bar", LoadingIndicator)
        loading_spinner.display = False
        
        if success:
            self.notify(message, title="Success!")
        else:
            self.notify(f"Engine Error: {message}", title="Oops!", severity="error")

def start():
    app = MoozeApp()
    app.run()

if __name__ == "__main__":
    start()