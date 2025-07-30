# YouTube-DL Library Usage Guide

## Overview
This document provides a quick reference for interacting with the youtube-dl library located in `youtube-dl-master/` folder.

## Core Components

### Main Class: `youtube_dl.YoutubeDL`
The primary interface for downloading videos from various platforms.

### Basic Usage Pattern
```python
import youtube_dl

# Create downloader with options
ydl_opts = {
    'outtmpl': '%(title)s.%(ext)s',  # Output filename template
    'format': 'best',                # Video quality
}

with youtube_dl.YoutubeDL(ydl_opts) as ydl:
    ydl.download(['https://youtube.com/watch?v=VIDEO_ID'])
```

## Key Configuration Options

| Option | Description | Example Values |
|--------|-------------|----------------|
| `outtmpl` | Output filename template | `'%(title)s.%(ext)s'`, `'downloads/%(id)s.%(ext)s'` |
| `format` | Video quality selection | `'best'`, `'worst'`, `'mp4'`, `'720p'` |
| `extractaudio` | Extract audio only | `True`/`False` |
| `audioformat` | Audio format when extracting | `'mp3'`, `'m4a'`, `'wav'` |
| `quiet` | Suppress console output | `True`/`False` |
| `no_warnings` | Disable warning messages | `True`/`False` |

## Key Methods

### `download(url_list)`
Downloads videos from provided URLs.
```python
ydl.download(['https://youtube.com/watch?v=VIDEO_ID'])
```

### `extract_info(url, download=True)`
Extracts video metadata. Set `download=False` to get info without downloading.
```python
info = ydl.extract_info(url, download=False)
title = info.get('title')
duration = info.get('duration')
```

### `prepare_filename(info_dict)`
Generates the output filename based on template and video info.
```python
filename = ydl.prepare_filename(info_dict)
```

## Platform Support
The library includes 900+ extractors in `youtube_dl/extractor/` supporting:
- YouTube
- Vimeo
- Facebook
- TikTok
- Instagram
- And many more...

## For Telegram Bot Integration

### Recommended Approach
1. Use `extract_info(url, download=False)` to get metadata first
2. Check video size/duration against Telegram limits
3. Use `download()` with custom `outtmpl` to control file location
4. Clean up downloaded files after uploading to Telegram

### Example Bot Integration
```python
ydl_opts = {
    'outtmpl': 'temp/%(id)s.%(ext)s',  # Temporary download location
    'format': 'best[filesize<50M]',    # Respect Telegram 50MB limit
    'quiet': True,
}

# Get info first
info = ydl.extract_info(url, download=False)
if info.get('filesize', 0) > 50 * 1024 * 1024:  # 50MB
    # Handle oversized video
    pass
else:
    # Download and upload to Telegram
    ydl.download([url])
```