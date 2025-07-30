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
        FIXED: Handle modern YouTube's separated video/audio streams properly.
        """
        video_formats = []
        audio_formats = []
        
        # Track format IDs to avoid TRUE duplicates only
        seen_video_format_ids = set()
        seen_audio_format_ids = set()
        
        # DEBUG: Log total formats and sample data to identify contamination issues
        logging.debug(f"Processing {len(raw_formats)} total formats from yt-dlp")
        
        for fmt in raw_formats:
            try:
                format_id = fmt.get('format_id', '')
                ext = fmt.get('ext', 'unknown')
                filesize = fmt.get('filesize') or fmt.get('filesize_approx', 0)
                
                # Skip if we've already processed this exact format
                if format_id in seen_video_format_ids or format_id in seen_audio_format_ids:
                    continue
                
                # Determine if this is video or audio-only
                vcodec = fmt.get('vcodec', 'none')
                acodec = fmt.get('acodec', 'none')
                
                # FIXED: Handle both combined and separated video/audio streams
                if vcodec != 'none':
                    # This is a video format (may or may not have audio)
                    height = fmt.get('height')
                    width = fmt.get('width')
                    fps = fmt.get('fps', 30)
                    
                    if height and height > 0:
                        # FIXED: Add validation to ensure height is reasonable (not preview data)
                        if not (240 <= height <= 4320):  # 240p to 8K range
                            logging.warning(f"Suspicious height {height}p for format {format_id} - might be preview data")
                            continue
                            
                        quality = f"{height}p"
                        
                        # DEBUG: Log format details to identify data source issues
                        logging.debug(f"Video format {format_id}: {quality}, size={filesize}, "
                                    f"vcodec={vcodec}, acodec={acodec}, ext={ext}")
                        
                        # Only track format IDs to avoid true duplicates
                        seen_video_format_ids.add(format_id)
                        
                        # FIXED: Don't estimate file sizes - they were wildly inaccurate (23x error rate)
                        # Only use actual file sizes from yt-dlp or set to 0 to avoid misleading users
                        if not filesize:
                            filesize = 0  # Don't show misleading estimates
                        
                        video_formats.append({
                            'quality': quality,
                            'format_id': format_id,
                            'ext': ext,
                            'filesize_mb': round(filesize / (1024 * 1024), 1) if filesize else 0,
                            'fps': fps,
                            'vcodec': vcodec,
                            'acodec': acodec,  # May be 'none' for video-only streams
                            'width': width,
                            'height': height,
                            'has_audio': acodec != 'none'
                        })
                        
                elif acodec != 'none' and vcodec == 'none':
                    # This is an audio-only format
                    abr = fmt.get('abr', 128)  # Audio bitrate
                    
                    # Only track format IDs, not arbitrary quality keys
                    seen_audio_format_ids.add(format_id)
                    
                    # FIXED: Don't estimate audio file sizes either - use actual values only
                    if not filesize:
                        filesize = 0  # Don't show misleading estimates
                    
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
        
        # Sort video formats by quality (highest first), then by preference
        video_formats.sort(key=lambda x: (
            self._quality_sort_key(x['quality']),  # Primary: quality
            x.get('has_audio', False),              # Secondary: prefer formats with audio
            x['ext'] == 'mp4',                     # Tertiary: prefer mp4
            -x.get('filesize_mb', 0)               # Quaternary: prefer larger files (better quality)
        ), reverse=True)
        
        # Deduplicate video formats - keep only the best format per quality
        unique_video_formats = []
        seen_qualities = set()
        for fmt in video_formats:
            quality = fmt['quality']
            if quality not in seen_qualities:
                seen_qualities.add(quality)
                unique_video_formats.append(fmt)
        
        # Sort audio formats by bitrate (highest first)
        audio_formats.sort(key=lambda x: x.get('abr', 0), reverse=True)
        
        return {
            'video': unique_video_formats,  # Return deduplicated list
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
                        format_selector = 'best'  # FIXED: Removed 720p limit
                logging.info(f"Downloading video from {url} with quality: {quality}")
            else:
                # Default format (backward compatibility) - FIXED: Removed 720p limit
                format_selector = 'best'
                logging.info(f"Downloading video from {url} with best available quality")
            
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