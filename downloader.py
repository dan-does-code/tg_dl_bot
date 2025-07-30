import os
import sys
import subprocess
import tempfile
import logging
import time
from pathlib import Path
import yt_dlp

class VideoDownloader:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        self.format_cache = {}  # Cache for format detection results
        
    def detect_available_formats(self, url):
        """
        Detect all available video qualities and formats for a given URL.
        Returns structured format data for user selection.
        
        Returns:
        {
            'title': str,
            'duration': int,
            'formats': {
                'video': [
                    {
                        'quality': '720p',
                        'format_id': 'format_id',
                        'ext': 'mp4',
                        'filesize_mb': 45,
                        'fps': 30,
                        'vcodec': 'avc1'
                    }
                ],
                'audio': [
                    {
                        'quality': 'audio_only',
                        'format_id': 'format_id',
                        'ext': 'm4a',
                        'filesize_mb': 8,
                        'abr': 128
                    }
                ]
            }
        }
        """
        try:
            # Check cache first (5 minute cache)
            cache_key = url
            current_time = time.time()
            
            if cache_key in self.format_cache:
                cached_data, timestamp = self.format_cache[cache_key]
                if current_time - timestamp < 300:  # 5 minutes
                    logging.debug(f"Format cache HIT for {url}")
                    return cached_data
                else:
                    # Remove expired cache entry
                    del self.format_cache[cache_key]
                    
            logging.info(f"Detecting formats for: {url}")
            
            # Configure yt-dlp for format detection only
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'noplaylist': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info without downloading
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    return None
                    
                # Extract basic video metadata
                title = info.get('title', 'Unknown')
                duration = info.get('duration', 0)
                
                # Process available formats
                raw_formats = info.get('formats', [])
                processed_formats = self._process_formats(raw_formats, duration)
                
                result = {
                    'title': title,
                    'duration': duration,
                    'formats': processed_formats
                }
                
                # Cache the result
                self.format_cache[cache_key] = (result, current_time)
                logging.debug(f"Format cache MISS - cached result for {url}")
                
                return result
                
        except Exception as e:
            logging.error(f"Format detection failed: {e}")
            return None
            
    def _process_formats(self, raw_formats, duration):
        """
        Process raw yt-dlp format data into structured format information.
        """
        video_formats = []
        audio_formats = []
        
        # Group formats by type and quality
        seen_video_qualities = set()
        seen_audio_qualities = set()
        
        for fmt in raw_formats:
            try:
                format_id = fmt.get('format_id', '')
                ext = fmt.get('ext', 'unknown')
                filesize = fmt.get('filesize') or fmt.get('filesize_approx', 0)
                
                # Determine if this is video or audio-only
                vcodec = fmt.get('vcodec', 'none')
                acodec = fmt.get('acodec', 'none')
                
                if vcodec != 'none' and acodec != 'none':
                    # Video format with audio
                    height = fmt.get('height')
                    width = fmt.get('width')
                    fps = fmt.get('fps', 30)
                    
                    if height:
                        quality = f"{height}p"
                        
                        # Skip if we already have this quality (prefer mp4 over webm)
                        quality_key = (quality, ext)
                        if quality in seen_video_qualities and ext != 'mp4':
                            continue
                            
                        seen_video_qualities.add(quality)
                        
                        # Estimate file size if not available
                        if not filesize and duration:
                            # Rough estimation based on quality
                            bitrate_estimate = self._estimate_bitrate(height)
                            filesize = (bitrate_estimate * duration) // 8  # Convert to bytes
                        
                        video_formats.append({
                            'quality': quality,
                            'format_id': format_id,
                            'ext': ext,
                            'filesize_mb': round(filesize / (1024 * 1024), 1) if filesize else 0,
                            'fps': fps,
                            'vcodec': vcodec,
                            'width': width,
                            'height': height
                        })
                        
                elif acodec != 'none' and vcodec == 'none':
                    # Audio-only format
                    abr = fmt.get('abr', 128)  # Audio bitrate
                    quality_key = f"audio_{abr}k"
                    
                    if quality_key not in seen_audio_qualities:
                        seen_audio_qualities.add(quality_key)
                        
                        # Estimate audio file size if not available
                        if not filesize and duration and abr:
                            filesize = (abr * 1000 * duration) // 8  # Convert kbps to bytes
                        
                        audio_formats.append({
                            'quality': 'audio_only',
                            'format_id': format_id,
                            'ext': ext,
                            'filesize_mb': round(filesize / (1024 * 1024), 1) if filesize else 0,
                            'abr': abr,
                            'acodec': acodec
                        })
                        
            except Exception as e:
                logging.warning(f"Error processing format {fmt.get('format_id', 'unknown')}: {e}")
                continue
        
        # Sort video formats by quality (highest first)
        video_formats.sort(key=lambda x: self._quality_sort_key(x['quality']), reverse=True)
        
        # Sort audio formats by bitrate (highest first)
        audio_formats.sort(key=lambda x: x.get('abr', 0), reverse=True)
        
        return {
            'video': video_formats,
            'audio': audio_formats
        }
        
    def _estimate_bitrate(self, height):
        """Estimate bitrate based on video height (resolution)"""
        bitrate_map = {
            2160: 20000,  # 4K
            1440: 10000,  # 1440p
            1080: 5000,   # 1080p
            720: 2500,    # 720p
            480: 1200,    # 480p
            360: 800,     # 360p
            240: 500,     # 240p
        }
        
        # Find closest resolution
        for res in sorted(bitrate_map.keys(), reverse=True):
            if height >= res:
                return bitrate_map[res]
        
        return 500  # Default for very low quality
        
    def _quality_sort_key(self, quality):
        """Convert quality string to numeric value for sorting"""
        try:
            return int(quality.replace('p', ''))
        except:
            return 0

    def download_video(self, url, format_id=None, quality=None):
        """
        Download video from URL with optional format selection.
        
        Args:
            url: Video URL to download
            format_id: Specific yt-dlp format ID to download
            quality: Quality string (e.g., '720p', 'audio_only') for backward compatibility
            
        Returns: (file_path, title, duration, file_size) or None if failed
        """
        try:
            # Output filename template
            output_template = os.path.join(self.temp_dir, "%(title)s.%(ext)s")
            
            # Determine format selector
            if format_id:
                # Use specific format ID
                format_selector = format_id
                logging.info(f"Downloading video from {url} with format ID: {format_id}")
            elif quality:
                # Convert quality to format selector
                if quality == 'audio_only':
                    format_selector = 'bestaudio/best'
                else:
                    # Extract height from quality (e.g., '720p' -> 720)
                    try:
                        height = int(quality.replace('p', ''))
                        format_selector = f'best[height<={height}]'
                    except:
                        format_selector = 'best[height<=720]'  # Default fallback
                logging.info(f"Downloading video from {url} with quality: {quality}")
            else:
                # Default format (backward compatibility)
                format_selector = 'best[height<=720]'
                logging.info(f"Downloading video from {url} with default quality")
            
            # Configure yt-dlp options
            ydl_opts = {
                'format': format_selector,
                'outtmpl': output_template,
                'noplaylist': True,
                'writeinfojson': True,
            }
            
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
                if file.suffix in ['.mp4', '.webm', '.mkv', '.avi', '.m4a', '.mp3']:
                    video_file = file
                elif file.suffix == '.json':
                    info_file = file
                    
            if not video_file:
                logging.error("No media file found after download")
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