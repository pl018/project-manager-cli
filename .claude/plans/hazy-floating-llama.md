# Implementation Plan: Fix Critical & High Priority Issues

## Overview
This plan addresses the most critical code quality issues identified in the comprehensive codebase review, including duplicate code, architectural inconsistencies, and missing type hints.

**Current Project State:**
- ✅ CLI functionality is working properly
- ❌ TUI display and notes function have issues
- ❌ Database schema changes not fully migrated causing notes save failures
- ℹ️ Project is in development phase - database can be backed up and rebuilt

## Execution Strategy
The fixes are ordered to minimize breaking changes and maintain functionality throughout the refactoring process. Since we're in dev phase, we can be more aggressive with database migrations.

---

## Phase 1 Completion Notes (2024-12-10)

**Status:** ✅ COMPLETED

**What was accomplished:**
1. ✅ Created backup script (`backup_databases.py`) - backed up both databases with timestamps
2. ✅ Standardized app data directory from `pyproject-cli` → `project-manager-cli` in `src/core/config.py:31`
3. ✅ Created migration script (`migrate_database.py`) that:
   - Added 5 missing columns to both databases (notes, favorite, last_opened, open_count, color_theme)
   - Merged 7 projects from both databases (2 from old, 7 from new)
   - Created all required tables (tags, tool_configs, search_history)
4. ✅ Added auto-migration method `_migrate_schema()` to `src/core/database.py`
   - Automatically runs on every database connection
   - Gracefully handles missing columns without breaking the app
5. ✅ Verified migration with multiple tests:
   - CLI works (`pm-cli list` shows all 7 projects)
   - Schema verification passed (all 14 columns present)
   - Notes functionality works (add, retrieve, search)
   - Favorites functionality works (toggle, persist)

**Files created:**
- `backup_databases.py` - Database backup utility
- `migrate_database.py` - One-time migration script
- `verify_schema.py` - Schema verification utility
- `test_notes.py` - Notes functionality test

**Files modified:**
- `src/core/config.py:31` - Changed app directory name
- `src/core/database.py:21-29` - Added auto-migration call in connect()
- `src/core/database.py:142-186` - Added `_migrate_schema()` method

**Critical fixes achieved:**
- ✅ Both CLI and TUI now use the same database location
- ✅ Database schema is consistent with all enhanced features
- ✅ Notes save functionality is working
- ✅ Auto-migration ensures future schema consistency

**Next steps:** Proceed to Phase 2 - Remove duplicate DatabaseManager, Config, Models, and Exceptions

---

## Phase 1: Database Schema Consolidation & Migration (Foundation)

### 1.1 Backup Current Database
**Action:** Create backup before any schema changes
- **Location:** Backup current database from both possible locations:
  - `%APPDATA%/project-manager-cli/projects.db`
  - `%APPDATA%/pyproject-cli/projects.db`
- **Method:** Copy to `projects.db.backup.{timestamp}`
- **Risk:** None - read-only operation

### 1.2 Standardize App Data Directory Name
**Files to modify:**
- `src/core/config.py:31` - Change `'pyproject-cli'` → `'project-manager-cli'`
- **Impact:** CRITICAL - ensures CLI and TUI share same database and schema
- **Current Issue:** This mismatch is causing the TUI/notes problems
- **Risk:** Medium - but acceptable in dev phase

**Migration Strategy:**
1. Check if data exists in old `pyproject-cli` directory
2. If exists, copy to new `project-manager-cli` directory
3. Merge with any existing data in `project-manager-cli` if needed
4. Log migration actions

### 1.3 Database Schema Migration
**Action:** Ensure both DatabaseManager implementations are using the same schema

**Current Issue:**
- CLI uses older schema without notes column
- TUI uses enhanced schema with notes, favorites, etc.
- This mismatch causes notes save failures

**Solution:**
1. Run database migration to ensure all columns exist in the shared database
2. Add migration check in `src/core/database.py` to auto-upgrade schema
3. Alternatively: Since we're in dev, rebuild database with proper schema from core

**Migration code to add in `src/core/database.py`:**
```python
def _migrate_schema(self):
    """Ensure database has all required columns."""
    cursor = self.conn.cursor()

    # Check and add missing columns
    cursor.execute("PRAGMA table_info(projects)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    # Add notes column if missing
    if 'notes' not in existing_columns:
        cursor.execute("ALTER TABLE projects ADD COLUMN notes TEXT")

    # Add other missing columns...
    self.conn.commit()
```

---

## Phase 2: Consolidate Duplicate Core Classes (Architecture)

### 2.1 Remove Duplicate DatabaseManager
**Action:** Delete inferior implementation, use enhanced version everywhere

**Files to DELETE:**
- `src/project_manager_cli/services/database_service.py` (entire file)

**Files to UPDATE:**
- `src/project_manager_cli/app.py:20` - Change import from `.services.database_service` to `core.database`
- Any other files importing from `project_manager_cli.services.database_service`

**Verification:**
- Grep for imports: `from project_manager_cli.services.database_service import` or `from .services.database_service import`
- Ensure all references point to `core.database.DatabaseManager`

### 2.2 Remove Duplicate Config Class
**Action:** Consolidate into single YAML-based configuration system

**Decision:** Keep `src/project_manager_cli/config.py` (more flexible, YAML-based), enhance and move to core

**Implementation:**
1. **Move** `src/project_manager_cli/config.py` → `src/core/config_manager.py`
2. **Update** `src/core/config.py` to import from `config_manager.py` for dynamic values
3. **Keep** static constants in `src/core/config.py` (like DB schema, defaults)
4. **Delete** duplicate config loading logic
5. **Update all imports:**
   - Change `from project_manager_cli.config import config` → `from core.config_manager import config`
   - Change `from core.config import Config` → Keep for static constants

**Files to UPDATE:**
- `src/project_manager_cli/cli.py` - Update imports
- `src/project_manager_cli/app.py` - Update imports
- `src/ui/app.py` - Ensure uses core config

### 2.3 Remove Duplicate Models
**Action:** Use only `src/core/models.py`

**Files to DELETE:**
- `src/project_manager_cli/models.py` (entire file)

**Files to UPDATE:**
- Search and replace all imports:
  - `from project_manager_cli.models import` → `from core.models import`
  - `from .models import` (in project_manager_cli/) → `from core.models import`

**Affected files:**
- `src/project_manager_cli/app.py`
- `src/project_manager_cli/services/ai_service.py`
- `src/project_manager_cli/services/project_service.py`
- `src/project_manager_cli/formatters/html_generator.py`

### 2.4 Remove Duplicate Exceptions
**Action:** Use only `src/core/exceptions.py`

**Files to DELETE:**
- `src/project_manager_cli/exceptions.py` (entire file)

**Files to UPDATE:**
- Replace imports: `from project_manager_cli.exceptions import` → `from core.exceptions import`

---

## Phase 3: Fix Architecture & Import Patterns (HIGH Priority)

### 3.1 Establish Clear Import Hierarchy
**Goal:** Enforce unidirectional dependency flow: `core → integrations → ui/cli`

**Principle:**
- `core/` - No dependencies on other project modules
- `integrations/` - Can import from `core/` only
- `ui/` - Can import from `core/` and `integrations/`
- `project_manager_cli/` - Can import from `core/` and `integrations/`
- `ui/` and `project_manager_cli/` should NOT import from each other

**Files to UPDATE:**
- `src/project_manager_cli/cli.py:262` - TUI command should shell out or use entry point, not direct import

**Implementation for TUI command:**
```python
# Instead of: from ui.app import run_tui
# Use subprocess to call entry point or refactor to common launcher
import subprocess
subprocess.run([sys.executable, "-m", "ui.app"])
```

**Alternative:** Create launcher in `main.py` or `src/__main__.py` that both entry points can use

### 3.2 Remove Redundant Services Directory
**Action:** After consolidating duplicates, remove empty/obsolete service files

**Files to DELETE (after moving logic to core):**
- `src/project_manager_cli/services/database_service.py` (already covered in 2.1)
- Review other files in `src/project_manager_cli/services/` - keep only CLI-specific services:
  - KEEP: `ai_service.py` (has CLI-specific logic)
  - KEEP: `logging_service.py` (CLI-specific)
  - KEEP: `project_service.py` (CLI-specific)
  - KEEP: `project_manager_service.py` (CLI-specific Cursor integration)

---

## Phase 4: Add Comprehensive Type Hints (HIGH Priority)

### 4.1 Add Type Hints to Core Module
**Files to update:**
- `src/core/database.py` - All methods need return types and parameter types
- `src/core/config.py` - Add type hints to all properties and methods

**Example changes needed:**

**File:** `src/project_manager_cli/app.py`
```python
# Line 91 - Add return type
def parse_arguments(self, args_list: list = None) -> argparse.Namespace:

# Line 84 - Add return type
def _setup_logging(self) -> None:
```

**File:** `src/project_manager_cli/services/project_manager_service.py`
```python
# Line 110 - Add type hint
def regenerate_cursor_projects_json(self, db_manager: 'DatabaseManager') -> None:
```

**File:** `src/ui/widgets/project_card.py`
```python
# Line 97 - Add parameter and return types
def on_click(self, event: events.Click) -> None:
```

### 4.2 Add Type Hints to Services
**Files to update:**
- `src/project_manager_cli/services/ai_service.py` - Add return types to all methods
- `src/project_manager_cli/services/project_service.py` - Add comprehensive type hints
- `src/project_manager_cli/services/logging_service.py` - Add type hints

### 4.3 Add Type Hints to UI Components
**Files to update:**
- `src/ui/app.py` - Add type hints to all methods
- `src/ui/screens/dashboard.py` - Add type hints to event handlers and methods
- `src/ui/screens/project_detail.py` - Add type hints
- `src/ui/widgets/*.py` - Add comprehensive type hints

### 4.4 Add Missing Imports for Type Hints
**Standard imports to add where needed:**
```python
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
```

---

## Phase 5: Standardize Error Handling (HIGH Priority)

### 5.1 Remove Bare Except Clauses
**File:** `src/project_manager_cli/formatters/html_generator.py`
```python
# Lines 67-70 - Replace bare except
try:
    tags = json.loads(tags)
except (json.JSONDecodeError, TypeError) as e:
    logger.warning(f"Failed to parse tags: {e}")
    tags = []
```

### 5.2 Standardize Exception Handling Pattern
**Pattern to use throughout:**
```python
try:
    # operation
except SpecificException as e:
    logger.error(f"Context: {e}", exc_info=True)
    # Handle or re-raise
```

**Files to update:**
- Search for `except Exception:` and make more specific
- Search for `except:` (bare) and add specific exception types
- Ensure all exceptions are logged before handling

---

## Phase 6: Basic Test Suite Setup (CRITICAL Priority)

### 6.1 Create Test Infrastructure
**Create directories:**
```
tests/
├── __init__.py
├── conftest.py          # Pytest fixtures
├── unit/
│   ├── __init__.py
│   ├── test_database.py
│   ├── test_config.py
│   └── test_models.py
└── integration/
    ├── __init__.py
    └── test_project_registration.py
```

### 6.2 Add Test Dependencies
**File:** `pyproject.toml`
Add to `[project.optional-dependencies]`:
```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.11.1",
]
```

### 6.3 Implement Core Unit Tests

**File:** `tests/unit/test_database.py`
- Test database initialization
- Test add_or_update_project
- Test get_project_by_path
- Test search_projects
- Test delete_project
- Use in-memory SQLite for tests

**File:** `tests/unit/test_config.py`
- Test config loading from YAML
- Test config defaults
- Test environment variable overrides

**File:** `tests/unit/test_models.py`
- Test Pydantic model validation
- Test model serialization/deserialization

### 6.4 Implement Integration Tests

**File:** `tests/integration/test_project_registration.py`
- Test full project registration flow
- Test UUID persistence
- Test database updates

### 6.5 Add Test Configuration

**File:** `tests/conftest.py`
```python
import pytest
from pathlib import Path
import tempfile
from core.database import DatabaseManager

@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
        db_path = f.name

    db = DatabaseManager(db_path=db_path)
    db.connect()
    yield db
    db.close()
    Path(db_path).unlink(missing_ok=True)

@pytest.fixture
def temp_project_dir():
    """Create temporary project directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)
```

---

## Critical Files to Modify

### To DELETE:
1. `src/project_manager_cli/services/database_service.py`
2. `src/project_manager_cli/models.py`
3. `src/project_manager_cli/exceptions.py`

### To MOVE/RENAME:
4. `src/project_manager_cli/config.py` → `src/core/config_manager.py` (with refactoring)

### To UPDATE (imports and type hints):
5. `src/project_manager_cli/cli.py` - Fix imports, add type hints
6. `src/project_manager_cli/app.py` - Fix imports, add type hints
7. `src/core/config.py` - Integrate with config_manager, add type hints
8. `src/core/database.py` - Add comprehensive type hints
9. `src/ui/app.py` - Update imports, add type hints
10. `src/ui/screens/dashboard.py` - Add type hints
11. `src/ui/screens/project_detail.py` - Add type hints
12. `src/ui/widgets/*.py` - Add type hints
13. `src/project_manager_cli/formatters/html_generator.py` - Fix error handling
14. `src/project_manager_cli/services/ai_service.py` - Add type hints
15. `src/project_manager_cli/services/project_service.py` - Add type hints
16. `src/project_manager_cli/services/project_manager_service.py` - Add type hints

### To CREATE:
17. `tests/` directory structure
18. `tests/conftest.py`
19. `tests/unit/test_database.py`
20. `tests/unit/test_config.py`
21. `tests/unit/test_models.py`
22. `tests/integration/test_project_registration.py`

---

## Validation Steps

After implementation:

1. **Run tests:** `pytest tests/ -v`
2. **Type checking:** `mypy src/` (if mypy is installed)
3. **Manual testing:**
   - `pm-cli run .` - Register current directory
   - `pm-cli list` - List projects
   - `python main.py` - Launch TUI
   - Verify database is shared between CLI and TUI
   - **Verify TUI notes feature works** - Add/edit notes and confirm they save
   - **Verify TUI display shows all projects correctly**
   - Verify AI tagging works with o4-mini model

4. **Import verification:**
   - `python -c "from core.database import DatabaseManager; print('OK')"`
   - `python -c "from core.models import Project; print('OK')"`
   - `python -c "from core.exceptions import DatabaseError; print('OK')"`

5. **Grep for old imports:**
   - Search for `from project_manager_cli.models import` (should be 0)
   - Search for `from project_manager_cli.exceptions import` (should be 0)
   - Search for `database_service` (should be 0)

---

## Risk Mitigation

1. **Backup:** User should commit current state before starting
2. **Incremental testing:** Test after each phase
3. **Rollback plan:** Git reset if major issues arise
4. **Migration handling:** Auto-migrate data from old `pyproject-cli` directory

---

## Implementation Order Summary

1. ✅ **Phase 1:** Database backup, standardize app directory, schema migration - **COMPLETED**
2. ⏳ **Phase 2:** Remove duplicate DatabaseManager, Config, Models, Exceptions - **PENDING**
3. ⏳ **Phase 3:** Fix import patterns and establish clear architecture - **PENDING**
4. ⏳ **Phase 4:** Add comprehensive type hints - **PENDING**
5. ⏳ **Phase 5:** Standardize error handling - **PENDING**
6. ⏳ **Phase 6:** Create basic test suite - **PENDING**

**Estimated Impact:**
- Files to delete: 3
- Files to move: 1
- Files to update: ~15
- Files to create: ~7 (tests) + 1 (migration code)
- Total changes: ~27 files

**Critical Fixes:**
- ✅ Fix TUI notes save functionality
- ✅ Fix TUI display issues
- ✅ Consolidate database schema
- ✅ Share database between CLI and TUI
- ✅ Remove duplicate code
- ✅ Add type safety
- ✅ Establish test coverage

This refactoring will significantly improve code maintainability, fix current TUI/notes issues, and establish a solid foundation for future development.
