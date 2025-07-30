# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Telegram Video Downloader Bot designed to download videos from online platforms (starting with YouTube). The project's core innovation is an intelligent `file_id` caching strategy that leverages Telegram's infrastructure to serve popular videos instantly after the first download, making the service highly efficient and cost-effective.

## Business Context

**Problem**: Users face inconvenient, ad-riddled third-party video downloaders. Developers face unsustainable bandwidth costs when every request requires re-downloading content.

**Solution**: Cache-first architecture using Telegram's `file_id` system:
- **Cache Miss**: Download video → Upload to user → Store `file_id` in database → Delete local file
- **Cache Hit**: Retrieve `file_id` from database → Telegram serves file directly (instant & free)

**Target KPI**: >80% cache hit rate for cost sustainability

## MVP Scope

**Core Features (Must Have)**:
- YouTube video link processing only
- Complete `file_id` caching implementation (both cache hit/miss paths)
- SQLite database for URL-to-`file_id` mapping
- Basic error handling for failed downloads

**Explicitly Out of Scope for MVP**:
- Other platforms (TikTok, Instagram, etc.)
- Job queue system for concurrent downloads
- Format/quality selection
- Playlist support

## Technology Stack

- **Language**: Python
- **Telegram Bot Library**: `python-telegram-bot` or `aiogram`
- **Download Engine**: `youtube-dl` library (located in `youtube-dl-master/`, see `youtube-dl-usage.md` for interaction guide)
- **Database**: SQLite for MVP → PostgreSQL for Phase 2
- **Deployment**: Railway PaaS (free tier constraints)

## Architecture Evolution

**MVP**: Single monolithic process with sequential processing
**Phase 2**: Add job queue (Celery + Redis) for concurrency, upgrade to PostgreSQL
**Long-term**: Multi-platform support, analytics dashboard

## Critical Constraints

- Must operate within Railway free-tier resource limits
- Telegram API limits: 50MB upload, 2GB download, rate limits
- `file_id` is bot-token specific (cannot share between bots)
- Platform ToS violations (personal use only)

## Key Risks & Mitigation

1. **`yt-dlp` breaks frequently** → Strategy needed for updates
2. **Resource overwhelm** → Job queue for Phase 2
3. **Cache miss spikes** → Monitor and potentially implement rate limiting

## Current State

Project contains:
- Formal project documentation in `docs/` directory:
  - `project-brief.md` - Executive summary and business context
  - `product-requirements.md` - Detailed functional requirements and user stories
  - `architecture.md` - Technical design and implementation guidance
- `youtube-dl` library in `youtube-dl-master/` folder
- Usage guide for youtube-dl in `youtube-dl-usage.md`
- No implementation code yet - ready for MVP development phase

## Documentation Structure

- `docs/project-brief.md` - Business case and high-level solution overview
- `docs/product-requirements.md` - Functional requirements and user stories
- `docs/architecture.md` - Database schema, workflows, and technical design
- `youtube-dl-usage.md` - Library interaction guide for development