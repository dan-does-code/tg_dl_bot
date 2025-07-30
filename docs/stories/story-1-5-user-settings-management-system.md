# Story 1.5: User Settings Management System

## Story
As a **bot user**,
I want **to configure my download preferences through a settings interface**,
so that **I can enable quick download mode with my preferred constraints**.

## Acceptance Criteria
1. Settings command opens interactive configuration interface
2. Users can set minimum/maximum quality constraints via button prompts
3. Users can set minimum/maximum file size constraints via button prompts
4. Settings are stored persistently per user and survive bot restarts
5. Settings interface shows current values and allows individual constraint modification

## Integration Verification
- IV1: Settings storage doesn't conflict with existing database operations
- IV2: Current user session management (if any) works with new settings persistence
- IV3: Settings interface performance doesn't impact core download functionality

## Dev Notes

### Current Bot Commands Analysis
From `bot.py:33-35`, current commands:
```python
self.application.add_handler(CommandHandler("start", self.start_command))
self.application.add_handler(CommandHandler("help", self.help_command))
self.application.add_handler(CommandHandler("stats", self.stats_command))
```

### Settings System Requirements
- Add `/settings` command to bot
- Create settings database table for user preferences
- Implement interactive settings interface using inline keyboards
- Support quality constraints (minimum/maximum resolution)
- Support file size constraints (minimum/maximum MB)
- Validate constraint logic (minimum <= maximum)
- Show current settings and allow individual modification

### Settings Data Model
```
user_settings table:
- user_id (INTEGER PRIMARY KEY)
- min_quality (TEXT) - e.g., "240p", "360p", etc.
- max_quality (TEXT) - e.g., "720p", "1080p", etc.
- min_file_size_mb (INTEGER) - minimum file size in MB
- max_file_size_mb (INTEGER) - maximum file size in MB
- quick_mode_enabled (BOOLEAN) - whether to use quick download mode
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
```

### Settings Interface Strategy
- Main settings menu with current values display
- Individual constraint setting workflows
- Quality selection using predefined resolution buttons
- File size input using numeric buttons or ranges
- Clear reset/disable options for each constraint
- Validation and error handling for invalid combinations

## Tasks

### Task 1: Database Schema for Settings
- [x] Create `user_settings` table with proper schema
- [x] Add methods for storing/retrieving user settings
- [x] Implement default settings handling
- [x] Add database migration for settings table

### Task 2: Settings Command and Interface
- [x] Add `/settings` command handler
- [x] Create main settings interface with current values
- [x] Implement constraint setting workflows
- [x] Add settings validation logic
- [x] Create settings reset/clear functionality

### Task 3: Quality Constraint Configuration
- [x] Implement minimum quality selection interface
- [x] Implement maximum quality selection interface
- [x] Add quality range validation (min <= max)
- [x] Handle edge cases (no available qualities in range)

### Task 4: File Size Constraint Configuration
- [x] Implement minimum file size setting interface
- [x] Implement maximum file size setting interface
- [x] Add file size range validation
- [x] Support reasonable file size limits (1MB - 50MB)

### Task 5: Settings Integration
- [x] Integrate settings with existing download flow
- [x] Add settings display in help command
- [x] Implement settings persistence across bot restarts
- [x] Add comprehensive error handling

## Testing
- Settings command functionality testing
- Constraint validation testing
- Settings persistence testing
- Edge case handling (invalid ranges, extreme values)
- Multi-user settings isolation testing

## Dev Agent Record

### Agent Model Used
- Claude Sonnet 4

### Debug Log References
- None yet

### Completion Notes
- Successfully implemented comprehensive user settings management system with interactive interface
- Added complete `/settings` command with multi-level navigation and constraint configuration
- Database schema includes user_settings table with proper indexing and default handling
- Interactive settings interface allows users to configure quality constraints (240p-1080p) and file size limits (1MB-50MB)
- Comprehensive validation prevents invalid constraint combinations (min > max scenarios)
- Quick mode toggle enables/disables automatic constraint-based downloads
- Settings persist across bot restarts and are isolated per user
- All edge cases handled: same min/max values, large user IDs, constraint clearing
- Auto-return navigation provides smooth user experience
- All tests pass including validation logic, database operations, and concurrent user scenarios

### File List
**Modified:**
- `bot.py` - Added complete settings system with interactive interface
  - Added `settings_command()` for /settings command handler
  - Added `create_settings_keyboard()` for main settings menu
  - Added `show_quality_selection()` and `show_size_selection()` for constraint setting
  - Added `handle_settings_callback()` for settings navigation
  - Added `handle_quality_set_callback()` and `handle_size_set_callback()` for constraint updates
  - Added `show_main_settings()` for navigation back to main menu
  - Added `_validate_quality_range()` for constraint validation
  - Enhanced callback query handler to support settings actions
  - Updated help command to include settings information

- `database.py` - Added complete user settings database functionality
  - Added `_create_user_settings_table()` for database schema
  - Added `get_user_settings()` for retrieving user preferences
  - Added `update_user_settings()` for updating individual settings
  - Added `clear_user_settings()` for resetting user preferences
  - Enhanced initialization to create settings table automatically

**Created:**
- `test_user_settings.py` - Database functionality test suite
- `test_settings_interface.py` - Interface and keyboard test suite  
- `test_settings_validation.py` - Validation logic and edge case test suite

### Change Log
| Date | Change | Notes |
|------|--------|-------|
| 2025-07-30 | Story created | Initial user settings management story |
| 2025-07-30 | Database schema | Created user_settings table and CRUD operations |
| 2025-07-30 | Settings command | Added /settings command and main interface |
| 2025-07-30 | Quality constraints | Implemented quality selection with validation |
| 2025-07-30 | File size constraints | Implemented file size selection with validation |
| 2025-07-30 | Validation logic | Added comprehensive constraint validation |
| 2025-07-30 | Testing completed | All test suites pass with comprehensive coverage |

### Status
Completed