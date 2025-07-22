import os
import subprocess
import argparse
import re
import sys

# --- Optional Colorama Import ---
try:
    # Attempt to import and initialize colorama
    from colorama import Fore, Style, init
    init(autoreset=True)
except ImportError:
    # If colorama is not installed create dummy objects so the script doesn't crash.
    print("Colorama not found. Proceeding without colored output.")
    class DummyColor:
        def __getattr__(self, name):
            return ""
    Fore = DummyColor()
    Style = DummyColor()

# --- Optional TQDM Import ---
try:
    from tqdm import tqdm
except ImportError:
    print(f"{Fore.RED}TQDM not found. Progress bars will not be displayed.")
    # Dummy class for tqdm lib if it's not available
    class tqdm:
        def __init__(self, total=None, desc=None, unit=None, unit_scale=None):
            self.total = total
            self.desc = desc
            self.n = 0
        def __enter__(self):
            print(f"Starting: {self.desc}")
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            print(f"Finished: {self.desc}")
        def update(self, n):
            pass # No-op if tqdm is not installed
        def close(self):
            pass # No-op

def get_video_duration(input_path):
    """Gets the duration of a video file in seconds using ffprobe."""
    command = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        input_path
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except FileNotFoundError:
        print(f"{Fore.RED}ERROR: 'ffprobe' command not found. Is FFmpeg installed and in your PATH?")
        return None
    except (subprocess.CalledProcessError, ValueError) as e:
        print(f"{Fore.RED}ERROR: Could not get duration for '{os.path.basename(input_path)}'.")
        print(f"{Fore.RED}ffprobe error: {e}")
        return None

def convert_videos_to_mp4(source_directory, dry_run=False):
    """
    Finds video files in a directory and coverters them to MP4 H264 using FFmpeg.
    """
    # Common video file extensions to look for
    video_extensions = ['.mkv', '.mov', '.avi', '.webm', '.flv', '.wmv']
    files_to_convert = []

    print(f"Scanning for video files in: {source_directory}")
    for root, _, files in os.walk(source_directory):
        for filename in files:
            # Check if video has an extension
            file_base, file_ext = os.path.splitext(filename)
            if file_ext.lower() in video_extensions:
                files_to_convert.append(os.path.join(root, filename))

    if not files_to_convert:
        print(f"{Fore.CYAN}No video found to convert.")
        return

    print(f"{Fore.GREEN}Found {len(files_to_convert)} video(s) to process.")

    if dry_run:
        print(f"\n{Fore.CYAN}--- DRY RUN MODE ---")
        print("The following conversions would be performed:")
        for input_path in files_to_convert:
            file_base, _ = os.path.splitext(input_path)
            output_path = f"{file_base}.mp4"
            print(f"  - Convert '{os.path.basename(input_path)}' -> '{os.path.basename(output_path)}'")
        print(f"{Fore.CYAN}--- END DRY RUN ---")
        return

    for input_path in files_to_convert:
        file_base, _ = os.path.splitext(input_path)
        output_path = f"{file_base}.mp4"
        filename = os.path.basename(input_path)

        print(f"{Fore.YELLOW}\nPreparing to convert '{filename}'...")

        # Get total duration for the progress bar
        duration = get_video_duration(input_path)
        if duration is None:
            continue # Skip file if duration can't be determined

        # Construct the FFmpeg command
        command = [
            'ffmpeg',
            '-y',                   # Overwrite output file if it exists
            '-i', input_path,       # Input file
            '-c:v', 'libx264',      # Video codec: H.264
            '-preset', 'slow',      # Encoding speed
            '-crf', '18',           # Constant Rate Factor (Lower is better quality)
            '-c:a', 'aac',          # Audio codec
            '-b:a', '128k',         # Audio Bitrate
            '-progress', 'pipe:1',  # Send progress to stdout
            '-nostats',             # Disable the default periodic stats printing (it didn't work in test anyways)
            output_path
        ]

        try:
            # Use Popen to run FFmpeg as a subprocess and read its stdout in real time
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, encoding='utf-8')

            # Regex to find the time in the progress output
            time_re = re.compile(r"out_time_ms=(\d+)")
            current_time = 0

            with tqdm(total=int(duration), desc=f"Converting {filename}", unit='s', unit_scale=True) as pbar:
                for line in process.stdout:
                    match = time_re.search(line)
                    if match:
                        elapsed_us = int(match.group(1))
                        elapsed_s = elapsed_us / 1_000_000
                        # Update the progress bar by the difference from the last update
                        pbar.update(elapsed_s - current_time)
                        current_time = elapsed_s

            # Wait for the process to finish and check for errors
            process.wait()
            if process.returncode != 0:
                error_output = process.stderr.read()
                print(f"{Fore.RED}ERROR converting '{filename}':")
                print(error_output)
            else:
                print(f"{Fore.GREEN}Successfully converted '{filename}' to '{os.path.basename(output_path)}'")

        except FileNotFoundError:
            print(f"{Fore.RED}ERROR: 'ffmpeg' command not found. Is ffmpeg installed and in your PATH?")
            return
        except Exception as e:
            print(f"{Fore.RED}An unexpected error has occurred during conversion of '{filename}': {e}")

    
    print(f"\n{Fore.GREEN}Conversion process complete.")

if __name__ == "__main__": 
    parser = argparse.ArgumentParser(description="Batch convert video files to MP4 (H.264/AAC) using FFmpeg.")
    parser.add_argument("directory", help="The directory containing video files to convert.")
    parser.add_argument("-d", "--dry-run", action="store_true", help="Scan for files and show what would be converted without actually running FFmpeg.")

    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print(f"{Fore.RED}ERROR: Directory not found at '{args.directory}'")
    else:
        convert_videos_to_mp4(args.directory, args.dry_run)
