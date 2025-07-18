import os
import subprocess
import argparse
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

def convert_videos_to_mp4(source_directory):
  """
  Finds video files in a directory and coverters them to MP4 H264 using FFmpeg.
  """
  # Common video file extensions to look for
  video_extensions = ['.mkv', '.mov', '.avi', '.webm', '.flv', '.wmv']

  print(f"Scanning for video files in: {source_directory}")

  for root, _, files in os.walk(source_directory):
      for filename in files:
          # Check if video has an extension and that it's not alread MP4
          file_base, file_ext = os.path.splitext(filename)
          if file_ext.lower() in video_extensions and file_ext.lower() != '.mp4':
              input_path = os.path.join(root, filename)
              output_path = os.path.join(root, f"{file_base}.mp4")

              print(f"\nConverting '{filename}'...")

              # Construct the FFmpeg command
              command = [
                  'ffmpeg',
                  '-i', input_path,      # Input file
                  '-c:v', 'libx264',     # Video codec: H.264
                  '-preset', 'slow',     # Encoding speed
                  '-crf', '18',          # Constant Rate Factor (Lower is better quality)
                  '-c:a', 'aac',         # Audio codec
                  '-b:a', '128k',        # Audio Bitrate
                  output_path
              ]

              try:
                  # 'capture_output=True' and 'text=True' will cpature stdout/stderr as text
                  result = subprocess.run(command, check=True, capture_output=True, text=True)
                  print(f"{Fore.GREEN}Successfully converted '{filename}' to '{os.path.basename(output_path)}'")
              except FileNotFoundError:
                  print(f"{Fore.RED}ERROR: 'ffmpeg' command not found. Is FFmpeg installed and in your PATH?")
                  return
              except subprocess.CalledProcessError as e:
                  # This error is rasied if FFmpeg returns a non-zero exit code (i.e., an error)
                  print(f"{Fore.RED}ERROR converting '{filename}':")
                  print(e.stderr) # print output for debugging

  print(f"{Fore.GREEN}\nConversion process complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch convert video files to MP4 (H.264/AAC) using FFmpeg.")
    parser.add_argument("directory", help="The directory containing video files to convert.")

    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print(f"{Fore.RED}ERROR: Directory not found at '{args.directory}'")
    else:
        convert_videos_to_mp4(args.directory)
