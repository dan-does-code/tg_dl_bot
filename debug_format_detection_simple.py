#!/usr/bin/env python3
"""
Debug script to test yt-dlp format detection directly
"""
import yt_dlp
import logging

logging.basicConfig(level=logging.INFO)

def test_format_detection(url):
    """Test format detection directly with yt-dlp"""
    print(f"\n[DEBUG] Testing format detection for: {url}")
    
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'noplaylist': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if not info:
                print("[ERROR] No info extracted")
                return
                
            print(f"[INFO] Title: {info.get('title', 'Unknown')}")
            print(f"[INFO] Duration: {info.get('duration', 0)} seconds")
            
            raw_formats = info.get('formats', [])
            print(f"[INFO] Total formats found: {len(raw_formats)}")
            
            # Analyze video formats
            video_qualities = set()
            audio_qualities = set()
            
            print("\n[VIDEO FORMATS]:")
            for fmt in raw_formats:
                vcodec = fmt.get('vcodec', 'none')
                acodec = fmt.get('acodec', 'none')
                
                if vcodec != 'none' and acodec != 'none':
                    height = fmt.get('height')
                    ext = fmt.get('ext', 'unknown')
                    format_id = fmt.get('format_id', '')
                    filesize = fmt.get('filesize') or fmt.get('filesize_approx', 0)
                    
                    if height:
                        quality = f"{height}p"
                        video_qualities.add(quality)
                        filesize_mb = round(filesize / (1024 * 1024), 1) if filesize else 0
                        print(f"  {quality} ({ext}) - ID: {format_id} - Size: {filesize_mb}MB")
            
            print(f"\n[SUMMARY] Unique video qualities: {sorted(video_qualities, key=lambda x: int(x.replace('p', '')), reverse=True)}")
            
            print("\n[AUDIO FORMATS]:")
            for fmt in raw_formats:
                vcodec = fmt.get('vcodec', 'none')
                acodec = fmt.get('acodec', 'none')
                
                if acodec != 'none' and vcodec == 'none':
                    abr = fmt.get('abr', 0)
                    ext = fmt.get('ext', 'unknown')
                    format_id = fmt.get('format_id', '')
                    filesize = fmt.get('filesize') or fmt.get('filesize_approx', 0)
                    
                    quality_key = f"audio_{abr}k"
                    audio_qualities.add(quality_key)
                    filesize_mb = round(filesize / (1024 * 1024), 1) if filesize else 0
                    print(f"  {abr}kbps ({ext}) - ID: {format_id} - Size: {filesize_mb}MB")
            
            print(f"\n[SUMMARY] Unique audio qualities: {len(audio_qualities)}")
            
    except Exception as e:
        print(f"[ERROR] {e}")

def test_current_implementation(url):
    """Test our current implementation"""
    print(f"\n[CURRENT] Testing VideoDownloader implementation:")
    
    from downloader import VideoDownloader
    downloader = VideoDownloader()
    
    result = downloader.detect_available_formats(url)
    
    if result:
        print(f"[INFO] Title: {result['title']}")
        print(f"[INFO] Duration: {result['duration']} seconds")
        print(f"[INFO] Video formats: {len(result['formats']['video'])}")
        print(f"[INFO] Audio formats: {len(result['formats']['audio'])}")
        
        print("\n[CURRENT VIDEO]:")
        for fmt in result['formats']['video']:
            print(f"  {fmt['quality']} ({fmt['ext']}) - ID: {fmt['format_id']} - Size: {fmt['filesize_mb']}MB")
            
        print("\n[CURRENT AUDIO]:")
        for fmt in result['formats']['audio']:
            print(f"  Audio ({fmt['ext']}) - ID: {fmt['format_id']} - Size: {fmt['filesize_mb']}MB - {fmt['abr']}kbps")
    else:
        print("[ERROR] Current implementation returned None")

if __name__ == "__main__":
    # Test URLs - more recent videos with multiple qualities
    test_urls = [
        "https://www.youtube.com/watch?v=BaW_jenozKc",  # YouTube official 4K video
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Classic test video (limited quality)
    ]
    
    print("STARTING FORMAT DETECTION DEBUG")
    print("=" * 50)
    
    for url in test_urls:
        print(f"\n{'='*20} DIRECT YT-DLP TEST {'='*20}")
        test_format_detection(url)
        
        print(f"\n{'='*20} CURRENT IMPLEMENTATION TEST {'='*20}")
        test_current_implementation(url)
        
        print("\n" + "="*70)