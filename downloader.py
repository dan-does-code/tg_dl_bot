import os
import sys
import subprocess
import tempfile
import logging
from pathlib import Path

class VideoDownloader:
    def __init__(self):
        # Get the path to youtube-dl executable
        self.youtube_dl_path = Path(__file__).parent / "youtube-dl-master" / "bin" / "youtube-dl"
        if not self.youtube_dl_path.exists():
            # Try alternative path
            self.youtube_dl_path = Path(__file__).parent / "youtube-dl-master" / "youtube_dl" / "__main__.py"
        
        self.temp_dir = tempfile.mkdtemp()
        
    def download_video(self, url):
        """
        Download video from URL and return local file path
        Returns: (file_path, title, duration, file_size) or None if failed
        """
        try:
            # Output filename template
            output_template = os.path.join(self.temp_dir, "%(title)s.%(ext)s")
            
            # Run youtube-dl to download video
            cmd = [
                sys.executable, str(self.youtube_dl_path),
                "--format", "best[height<=720]",  # Limit quality for Telegram compatibility
                "--output", output_template,
                "--no-playlist",
                "--write-info-json",
                url
            ]
            
            logging.info(f"Running youtube-dl command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                logging.error(f"youtube-dl failed: {result.stderr}")
                return None
                
            # Find downloaded files
            temp_files = list(Path(self.temp_dir).glob("*"))
            video_file = None
            info_file = None
            
            for file in temp_files:
                if file.suffix in ['.mp4', '.webm', '.mkv', '.avi']:
                    video_file = file
                elif file.suffix == '.info.json':
                    info_file = file
                    
            if not video_file:
                logging.error("No video file found after download")
                return None
                
            # Extract metadata from info file if available
            title = video_file.stem
            duration = None
            file_size = video_file.stat().st_size
            
            if info_file:
                try:
                    import json
                    with open(info_file, 'r', encoding='utf-8') as f:
                        info = json.load(f)
                        title = info.get('title', title)
                        duration = info.get('duration')
                except Exception as e:
                    logging.warning(f"Could not parse info file: {e}")
                    
            return str(video_file), title, duration, file_size
            
        except subprocess.TimeoutExpired:
            logging.error("Download timed out")
            return None
        except Exception as e:
            logging.error(f"Download failed: {e}")
            return None
            
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception as e:
            logging.warning(f"Could not clean up temp files: {e}")
            
    def __del__(self):
        self.cleanup_temp_files()