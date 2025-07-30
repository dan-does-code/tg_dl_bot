# Story 1.2: Enhanced Video Format Detection

## Story
As a **bot user**,
I want **the system to detect all available video qualities and formats before presenting options**,
so that **I can make informed choices about download quality and format**.

## Acceptance Criteria
1. yt-dlp integration extracts available formats without downloading content
2. Format information includes resolution, file size estimates, and format type
3. Audio-only option is identified and presented when available
4. Format detection completes within 5 seconds for supported URLs
5. Detection results are cached temporarily to avoid repeated API calls

## Integration Verification
- IV1: Existing video download functionality remains intact if format detection fails
- IV2: Current error handling patterns are preserved for invalid URLs
- IV3: Format detection doesn't impact existing direct download workflows

## Dev Notes

### Current Download Implementation Analysis
From `downloader.py:23-39`, current implementation:
```python
ydl_opts = {
    'format': 'best[height<=720]',  # Limit quality for Telegram compatibility
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
```

### Enhanced Format Detection Requirements
- Use `yt_dlp.extract_info(url, download=False)` to get format list
- Parse `info['formats']` to extract available qualities and formats
- Identify video formats (mp4, webm) vs audio formats (m4a, mp3)
- Estimate file sizes from format data
- Cache format detection results for 5 minutes to avoid repeated API calls

### Format Detection Strategy
1. Extract all formats using yt-dlp without downloading
2. Filter and categorize formats (video vs audio)
3. Extract quality information (resolution, bitrate)
4. Estimate file sizes from available metadata
5. Return structured format data for user selection

## Tasks

### Task 1: Implement Format Detection Core
- [x] Create `detect_available_formats()` method in VideoDownloader
- [x] Parse yt-dlp format data to extract quality information
- [x] Categorize formats into video and audio types
- [x] Handle edge cases where format data is incomplete

### Task 2: Add Format Information Enrichment
- [x] Extract resolution information (240p, 360p, 480p, 720p, etc.)
- [x] Estimate file sizes from bitrate and duration when available
- [x] Identify best quality options for each resolution
- [x] Add format compatibility checks (mp4 preferred over webm)

### Task 3: Implement Format Detection Caching
- [x] Add temporary caching mechanism for format detection results
- [x] Cache format data for 5 minutes to avoid repeated API calls
- [x] Implement cache cleanup for memory management
- [x] Add cache hit/miss metrics

### Task 4: Integration and Error Handling
- [x] Integrate format detection with existing download workflow
- [x] Ensure existing download functionality works if format detection fails
- [x] Add comprehensive error handling for network issues
- [x] Test performance with various video URLs

## Testing
- Unit tests for format parsing logic
- Integration tests with real YouTube URLs
- Performance tests for 5-second timeout requirement
- Error handling tests for invalid URLs and network issues

## Dev Agent Record

### Agent Model Used
- Claude Sonnet 4

### Debug Log References
- None yet

### Completion Notes
- Successfully implemented comprehensive format detection using yt-dlp without downloading content
- Format detection extracts resolution, file size estimates, codec information, and format types
- Implemented 5-minute caching mechanism to avoid repeated API calls for same URL
- Enhanced download_video method to support specific format_id and quality selection
- Comprehensive error handling for network issues and invalid URLs
- All unit tests pass - format processing, quality sorting, bitrate estimation, and caching work correctly
- Backward compatibility maintained - existing download calls continue to work unchanged

### File List
**Modified:**
- `downloader.py` - Enhanced VideoDownloader class with format detection and caching

**Created:**
- `test_format_detection.py` - Comprehensive integration test suite (network-dependent)
- `test_format_detection_unit.py` - Unit test suite for format processing logic

### Change Log
| Date | Change | Notes |
|------|--------|-------|
| 2025-07-30 | Story created | Initial format detection enhancement story |
| 2025-07-30 | Core implementation | Added detect_available_formats() method with format processing |
| 2025-07-30 | Caching added | Implemented 5-minute cache for format detection results |
| 2025-07-30 | Download enhancement | Enhanced download_video() to support format selection |
| 2025-07-30 | Testing completed | All unit tests pass, integration tests created |

### Status
Ready for Review