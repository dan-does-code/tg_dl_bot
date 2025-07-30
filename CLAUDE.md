# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository using the BMad-Method framework.

## 🧙 BMad-Method Framework Integration

**CRITICAL**: This project strictly follows the **BMad-Method** (Breakthrough Method of Agile AI-driven Development) framework. Claude Code must operate as specialized BMad agents when working on this project.

### BMad Agent System Available

The `web-bundles/` directory contains all BMad-Method agents and resources:

**Core Agents**:
- `bmad-master` - Universal task executor for any domain
- `bmad-orchestrator` - Team coordinator for multi-agent workflows
- `analyst` - Business analysis and requirements gathering
- `architect` - Technical architecture and system design  
- `dev` - Development implementation and coding
- `pm` - Project management and planning
- `po` - Product owner and feature prioritization
- `qa` - Quality assurance and testing
- `sm` - Scrum master and story creation
- `ux-expert` - User experience design

**How to Activate BMad Agents**:
1. Copy content from `web-bundles/agents/{agent-name}.txt`
2. Paste into Claude Code conversation
3. Agent will activate with specialized persona and commands
4. Use agent-specific commands (prefixed with `*`)

### BMad Agent Selection Guide

**For This Project**:
- **Planning Phase**: Use `pm` or `architect` agents
- **Requirements**: Use `analyst` or `po` agents  
- **Implementation**: **ALWAYS** use `dev` agent for coding
- **Story Creation**: **ALWAYS** use `sm` agent
- **Architecture Decisions**: Use `architect` agent
- **Multi-agent Coordination**: Use `bmad-orchestrator`
- **General Tasks**: Use `bmad-master` (but prefer specialized agents)

**NEVER use `bmad-master` or `bmad-orchestrator` for**:
- Story creation (use `sm` agent)
- Code implementation (use `dev` agent)

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
- **Telegram Bot Library**: `python-telegram-bot` 
- **Download Engine**: `yt-dlp` library (modern replacement for youtube-dl)
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

**✅ COMPLETED**:
- Core bot implementation (`bot.py`, `downloader.py`, `database.py`)
- BMad-Method framework integration (`web-bundles/` directory)
- Working video download functionality with yt-dlp
- Cache system with SQLite database
- Error handling and file size validation

**📁 Project Structure**:
- `docs/` - Formal project documentation
- `web-bundles/` - BMad-Method agents and resources
- `bot.py` - Main Telegram bot implementation
- `downloader.py` - Video download logic using yt-dlp
- `database.py` - SQLite caching system
- `requirements.txt` - Python dependencies

## BMad-Method Commands Reference

**When using any BMad agent**, common commands include:
- `*help` - Show agent-specific commands
- `*kb` - Toggle knowledge base mode
- `*task {task}` - Execute specific tasks
- `*create-doc {template}` - Create documents from templates
- `*exit` - Exit agent mode

**Example BMad Workflow**:
1. Activate `pm` agent for project planning
2. Switch to `architect` agent for technical design
3. Switch to `dev` agent for implementation
4. Switch to `qa` agent for testing strategy

## Development Guidelines

**MUST follow BMad-Method**:
- Always activate appropriate BMad agent for the task
- Use agent-specific commands and workflows
- Follow BMad documentation patterns
- Maintain agent persona consistency

**Code Quality**:
- Follow existing code conventions
- Implement proper error handling
- Add logging for debugging
- Test functionality before committing