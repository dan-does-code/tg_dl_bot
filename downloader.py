import os
import sys
import subprocess
import tempfile
import logging
from pathlib import Path
import yt_dlp

class VideoDownloader:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        
    def download_video(self, url):
        """
        Download video from URL and return local file path
        Returns: (file_path, title, duration, file_size) or None if failed
        """
        try:
            # Output filename template
            output_template = os.path.join(self.temp_dir, "%(title)s.%(ext)s")
            
            # Configure yt-dlp options
            ydl_opts = {
                'format': 'best[height<=720]',  # Limit quality for Telegram compatibility
                'outtmpl': output_template,
                'noplaylist': True,
                'writeinfojson': True,
            }
            
            logging.info(f"Downloading video from: {url}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info first to get metadata
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'Unknown')
                duration = info.get('duration')
                
                # Now download the video
                ydl.download([url])
                
            # Find downloaded files
            temp_files = list(Path(self.temp_dir).glob("*"))
            video_file = None
            info_file = None
            
            for file in temp_files:
                if file.suffix in ['.mp4', '.webm', '.mkv', '.avi']:
                    video_file = file
                elif file.suffix == '.json':
                    info_file = file
                    
            if not video_file:
                logging.error("No video file found after download")
                return None
                
            file_size = video_file.stat().st_size
            
            return str(video_file), title, duration, file_size
            
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