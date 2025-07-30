# Story 1.1: Database Schema Enhancement with Migration

## Story
As a **system administrator**,
I want **the database schema to support compound cache keys (URL + quality + format) while preserving existing cache data**,
so that **the enhanced caching system works efficiently without losing valuable cached content**.

## Acceptance Criteria
1. New database schema supports storing cache entries with URL, quality, format, and file_id
2. Migration script successfully converts existing URL-only cache entries to new schema format
3. Existing cache lookup functionality continues to work during and after migration
4. New compound key lookup functionality is implemented and tested
5. Database indexes are optimized for both legacy and new lookup patterns

## Integration Verification
- IV1: All existing cached videos remain accessible via existing file_ids after migration
- IV2: Current cache hit functionality continues working without performance degradation  
- IV3: New cache storage doesn't break existing URL-based lookups during transition period

## Dev Notes

### Current Database Schema Analysis
From `database.py:15-26`, the current schema is:
```sql
CREATE TABLE IF NOT EXISTS video_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,
    file_id TEXT NOT NULL,
    title TEXT,
    duration INTEGER,
    file_size INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Enhanced Schema Requirements
Need to support compound keys: URL + quality + format while maintaining backward compatibility.

### Migration Strategy
1. Add new columns to support quality/format
2. Migrate existing entries to new schema
3. Update lookup functions to support both legacy and new patterns
4. Maintain existing performance characteristics

## Tasks

### Task 1: Design Enhanced Database Schema
- [x] Design new schema supporting compound keys (URL + quality + format)
- [x] Ensure backward compatibility with existing URL-only entries
- [x] Plan migration path for existing data

### Task 2: Implement Migration Script
- [x] Create migration function to add new columns
- [x] Populate default values for existing entries
- [x] Test migration with sample data

### Task 3: Update Database Manager Class
- [x] Add new methods for compound key lookups
- [x] Maintain backward compatibility with existing methods
- [x] Update indexing strategy

### Task 4: Test Migration and Functionality
- [x] Test migration preserves existing data
- [x] Test new compound key functionality
- [x] Test backward compatibility
- [x] Performance testing for new indexes

## Testing
- Unit tests for migration script
- Integration tests for backward compatibility
- Performance tests for new lookup patterns
- Test with sample existing cache data

## Dev Agent Record

### Agent Model Used
- Claude Sonnet 4

### Debug Log References
- None yet

### Completion Notes
- Successfully implemented enhanced database schema with compound keys (URL + quality + format)
- Migration preserves all existing data while enabling new functionality
- Backward compatibility maintained - existing code continues to work unchanged
- New methods added for compound key operations: `get_cached_file_id_compound()` and `store_cached_file_id_compound()`
- Enhanced statistics now show breakdown by quality and format
- Comprehensive test suite validates migration and new functionality

### File List
**Modified:**
- `database.py` - Enhanced DatabaseManager class with compound key support

**Created:**
- `test_database_migration.py` - Comprehensive test suite for migration and functionality

### Change Log
| Date | Change | Notes |
|------|--------|-------|
| 2025-07-30 | Story created | Initial database schema enhancement story |
| 2025-07-30 | Schema designed | Compound key schema with migration strategy |
| 2025-07-30 | Migration implemented | Table recreation approach preserves data |
| 2025-07-30 | Methods updated | New compound key methods with backward compatibility |
| 2025-07-30 | Testing completed | All migration and functionality tests pass |

### Status
Ready for Review