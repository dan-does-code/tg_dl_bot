# Telegram Video Downloader Bot Product Requirements Document (PRD)

## Goals and Background Context

### Goals
*   To create a Telegram bot that allows users to download videos from YouTube by sending a link.
*   To implement a `file_id` caching system to minimize server costs and provide instant delivery for popular videos.
*   To build a functional MVP that operates within the limits of a free-tier hosting plan (e.g., Railway).
*   To establish a foundation that can be expanded to support more platforms and features in the future.

### Background Context
This project aims to solve the common user need of downloading online videos in a simple, secure, and ad-free manner. The primary technical challenge for such a service is the operational cost associated with bandwidth and processing.

Our core strategy is to use Telegram's own infrastructure as a free, distributed cache. When a video is requested for the first time, our bot will download it using `yt-dlp`, send it to the user, and store the `file_id` provided by Telegram in our database. All subsequent requests for that same video will be fulfilled instantly by sending this `file_id`, eliminating any load on our server. This makes the service exceptionally fast for users and cost-effective to operate.

### Change Log
| Date       | Version | Description              | Author |
| :--------- | :------ | :----------------------- | :----- |
| [Current Date] | 1.0     | Initial PRD draft.       | John   |

## Requirements

### Functional
1.  **FR1:** The bot MUST accept and correctly parse valid YouTube video URLs.
2.  **FR2:** The bot MUST implement a "cache miss" workflow: if a URL is not in the database, it shall download the video, upload it to Telegram, and store the resulting `file_id` mapped to the URL.
3.  **FR3:** The bot MUST implement a "cache hit" workflow: if a URL is found in the database, it shall send the video to the user using the stored `file_id`.
4.  **FR4:** The bot MUST respond to a `/start` command with a brief, welcoming message explaining its function.
5.  **FR5:** The bot MUST send the video file to the user upon a successful download.
6.  **FR6:** The bot MUST send a user-friendly error message if a video download fails for any reason (e.g., private video, invalid link).

### Non Functional
1.  **NFR1:** The service MUST be deployable and operable within the resource constraints of Railway's free tier for the MVP.
2.  **NFR2:** Responses for "cache hit" requests SHOULD be delivered to the user in under 2 seconds.
3.  **NFR3:** The database for the MVP WILL be SQLite.
4.  **NFR4:** The system MUST handle videos up to Telegram's bot upload limit of 50 MB and provide a clear error for files exceeding this limit.
5.  **NFR5:** Basic operational events (request received, cache hit/miss, success/failure) MUST be logged for debugging purposes.

## User Interface Design Goals
This project is a service-based bot and does not have a graphical user interface (GUI). This section is not applicable.

## Technical Assumptions
*   **Repository Structure:** Single Repository.
*   **Service Architecture:** A single, monolithic Python process for the MVP.
*   **Testing Requirements:** Unit tests will be created for core logic, including URL parsing, database interaction, and the caching decision logic.
*   **Additional Technical Assumptions:** The bot will be built using Python, leveraging the `python-telegram-bot` (or `aiogram`) and `yt-dlp` libraries.

## Epic List
*   **Epic 1: MVP - YouTube Video Downloader with Caching:** Establish the core bot functionality, including receiving links, implementing the complete cache-miss and cache-hit logic for YouTube, and handling basic user interactions and errors.

## Epic 1: MVP - YouTube Video Downloader with Caching
This epic covers all work required to launch a functional, efficient bot that can handle YouTube links. The goal is to successfully implement the `file_id` caching architecture and provide a reliable service for the initial user base.

### Story 1.1: Bot Setup and Welcome
*As a user, I want to start the bot and receive a welcome message, so that I know it's active and understand how to use it.*

**Acceptance Criteria:**
1.  The bot successfully connects to the Telegram API using its token.
2.  When a user sends the `/start` command, the bot replies with a simple, informative welcome message.
3.  The welcome message briefly explains that the user should send a YouTube link.

### Story 1.2: Implement Cache Miss Logic
*As the system, I want to process a new, unique YouTube link by downloading the video and storing its `file_id`, so that it can be cached for future requests.*

**Acceptance Criteria:**
1.  When a new YouTube URL is received, the system correctly identifies it is not in the database.
2.  The system uses `yt-dlp` to download the corresponding video file to the server's temporary storage.
3.  The system successfully uploads the video file to the user via the Telegram API.
4.  The system correctly captures the `file_id` from the successful upload response.
5.  The system saves the URL and its corresponding `file_id` into the SQLite database.
6.  The temporary video file is deleted from the server after the process is complete.

### Story 1.3: Implement Cache Hit Logic
*As the system, I want to process a previously seen YouTube link by using its stored `file_id`, so that the video is delivered instantly and efficiently.*

**Acceptance Criteria:**
1.  When a previously seen YouTube URL is received, the system correctly finds its corresponding `file_id` in the database.
2.  The system sends the video to the user by passing the `file_id` directly to the Telegram API.
3.  The video is delivered without being re-downloaded or stored on our server.

### Story 1.4: Link Processing and Orchestration
*As a user, I want to send any valid YouTube link to the bot, so that it is automatically processed using the correct caching logic.*

**Acceptance Criteria:**
1.  The bot correctly identifies and extracts YouTube URLs from user messages.
2.  The bot queries the database to determine if the URL is a "cache miss" or "cache hit".
3.  The bot correctly triggers the "cache miss" workflow (Story 1.2) for new URLs.
4.  The bot correctly triggers the "cache hit" workflow (Story 1.3) for existing URLs.
5.  The bot ignores any text that is not a valid YouTube URL.

### Story 1.5: Basic Error Handling
*As a user, I want to receive a clear message if my video can't be downloaded, so that I understand there was a problem.*

**Acceptance Criteria:**
1.  If `yt-dlp` fails to download a video (e.g., it's private, region-locked), the bot sends a specific error message to the user.
2.  If a downloaded video exceeds the 50 MB Telegram upload limit, the bot sends an error message explaining the issue.
3.  The bot does not crash or hang if a download fails.

## Checklist Results Report
This section will be populated by the Product Owner (PO) upon validation of this PRD against the master checklist.

## Next Steps

### UX Expert Prompt
This project does not require a UX Expert as it has no GUI.

### Architect Prompt
"Winston, please review this PRD. Your task is to create a detailed Architecture Document that outlines the technical design for this Telegram bot. Please focus on:
1.  The final database schema for the SQLite table.
2.  A clear diagram of the application flow, including the cache-hit/miss logic.
3.  The proposed Python project structure.
4.  A strategy for managing dependencies, especially for keeping `yt-dlp` updated.
5.  An error handling strategy that covers the scenarios in Story 1.5."