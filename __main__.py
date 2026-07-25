import argparse
import sys
import subprocess
import shutil

# App version
__version__ = "1.2.0"

def upgrade_mooze():
    """Self-upgrades the app and all its dependencies via pip."""
    print("Checking for updates for Mooze, FFmpeg, and dependencies...")
    try:
        # sys.executable ensures we use the exact python environment Mooze is running in
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "mooze"])
        print("\nSuccess! Mooze and its dependencies are up to date.")
    except subprocess.CalledProcessError:
        print("\nError: Failed to upgrade. Check your internet connection or permissions.")
    sys.exit(0)

def get_ffmpeg_path():
    """Detects system FFmpeg, or falls back to the pip-installed version."""
    # 1. Check if FFmpeg is already installed globally on the user's system
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
        
    # 2. If not globally installed, use the PyPI bundled version
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return None

def main():
    parser = argparse.ArgumentParser(description="Mooze - Terminal Audio Downloader")
    
    # Add the version flag (-v, --version)
    parser.add_argument("-v", "--version", action="version", version=f"Mooze v{__version__}")
    
    # Add the upgrade flag
    parser.add_argument("--upgrade", action="store_true", help="Upgrade Mooze and its dependencies to the latest version")
    
    # Parse arguments (parse_known_args allows Textual to handle any other args later if needed)
    args, unknown = parser.parse_known_args()

    # Trigger upgrade if requested
    if args.upgrade:
        upgrade_mooze()

    # Resolve FFmpeg
    ffmpeg_path = get_ffmpeg_path()
    if not ffmpeg_path:
        print("Critical Error: FFmpeg could not be found or downloaded.")
        sys.exit(1)

    # TODO: Start your Textual app here!
    # print(f"Starting Mooze... (using FFmpeg at: {ffmpeg_path})")
    # app = MoozeApp(ffmpeg_location=ffmpeg_path)
    # app.run()

if __name__ == "__main__":
    main()