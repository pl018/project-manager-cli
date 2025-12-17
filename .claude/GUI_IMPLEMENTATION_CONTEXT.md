# GUI Implementation Context - Quick Start

## What We're Implementing

**Goal**: Enhance the PySide6 desktop GUI (`src/project_manager_desktop/`) with Edit and Docs tabs.

**Implementation Plan**: `.claude/plans/gui-enhancements.md` (~3.5 hours)

## Current GUI State

**Location**: `src/project_manager_desktop/`
- `main.py` - Entry point (`pm-gui` command)
- `window.py` - MainWindow with tabs
- `models.py` - Qt table models

**Existing Tabs**:
- ✅ Overview (read-only metadata)
- ✅ Notes (editable with save/revert)
- ✅ Tools (open in IDEs)
- ⚠️ Docs (PLACEHOLDER - just a label)

**Missing**:
- ❌ Edit tab (name, description, tags)
- ❌ Functional Docs tab (markdown browser)
- ❌ Delete button

## Implementation Order (From Plan)

### Phase 1: Infrastructure (30 min) - START HERE
1. Add `DocFile` model to `src/core/models.py`
2. Add `update_project_fields()` to `src/core/database.py`
3. Add `open_file()` to `src/integrations/base.py`
4. Implement `open_file()` in `src/integrations/cursor.py`

### Phase 2: Doc Discovery Service (20 min)
5. Create `src/project_manager_cli/services/docs_discovery_service.py`
6. Test doc discovery independently

### Phase 3: Tag Editor Widget (30 min)
7. Create `src/project_manager_desktop/widgets/__init__.py`
8. Create `src/project_manager_desktop/widgets/tag_editor.py`

### Phase 4: Edit Tab (40 min)
9. Add Edit tab to `window.py`
10. Wire up form fields, save/cancel

### Phase 5: Docs Tab (60 min)
11. Replace Docs tab placeholder in `window.py:154-163`
12. Implement file table, markdown preview
13. Wire up file opening

### Phase 6: Polish (30 min)
14. Add delete functionality
15. Test end-to-end
16. Error handling

## Critical Files

**Must Modify**:
- `src/project_manager_desktop/window.py` ⭐ CRITICAL
- `src/core/database.py`
- `src/core/models.py`
- `src/integrations/base.py`
- `src/integrations/cursor.py`

**Must Create**:
- `src/project_manager_desktop/widgets/__init__.py`
- `src/project_manager_desktop/widgets/tag_editor.py`
- `src/project_manager_cli/services/docs_discovery_service.py`

## Key Technical Details

### Database
- No schema changes needed (all fields exist)
- New method: `update_project_fields(uuid, **fields)`
- Fields: `ai_app_name`, `description`, `tags`, `last_updated`

### DocFile Model
```python
class DocFile(BaseModel):
    filename: str
    full_path: Path
    relative_path: str
    extension: str
    size_bytes: int
    modified_date: datetime
```

### Doc Discovery
- Extensions: `.md`, `.markdown`
- Exclude: node_modules, venv, .git, __pycache__, dist, build
- Max: 500 files
- Sort: README first, then alphabetical

### Markdown Rendering (Qt)
- Use `QTextBrowser` for preview
- Convert markdown to HTML with `markdown` library
- Extensions: fenced_code, tables, nl2br

## Dependencies to Add

**Required**:
- `markdown` - For markdown to HTML conversion

**Optional**:
- `pygments` - Syntax highlighting
- `pymdown-extensions` - Enhanced markdown

## Shared with TUI

These changes will be used by both GUI and TUI:
- `DocFile` model
- `update_project_fields()` method
- `open_file()` integration methods
- `docs_discovery_service.py`

## Quick Commands

```bash
# Test the GUI
pm-gui

# Or directly
python -m project_manager_desktop.main

# Check database location
pm-cli config
```

## What to Tell Claude

When starting the new chat, say:

> "I want to implement the GUI enhancements for the Project Manager CLI desktop application. The implementation plan is in .claude/plans/gui-enhancements.md. Please read the plan and the context file at .claude/GUI_IMPLEMENTATION_CONTEXT.md, then let's start with Phase 1 (Infrastructure) as outlined in the plan."

## Expected Workflow

1. Read this context + implementation plan
2. Implement Phase 1 (infrastructure layer)
3. Test infrastructure changes
4. Implement Phase 2 (doc discovery)
5. Test doc discovery
6. Implement Phase 3 (tag editor widget)
7. Implement Phase 4 (Edit tab)
8. Test Edit tab
9. Implement Phase 5 (Docs tab)
10. Test Docs tab
11. Implement Phase 6 (polish & delete)
12. Full end-to-end testing

## Success Criteria

- ✅ Edit tab allows editing name, description, tags
- ✅ Changes persist to database
- ✅ Docs tab shows markdown files with preview
- ✅ Can open files in Cursor
- ✅ Delete button with confirmation
- ✅ No crashes or errors
- ✅ Changes visible in CLI/TUI (shared database)

## Notes

- PySide6 uses Qt signals/slots (not Textual messages)
- Use `QFormLayout` for form fields
- Use `QTableView` or `QTableWidget` for file list
- Use `QTextBrowser` for markdown preview
- Remember to call `_ensure_db()` before database operations
- Update status bar with helpful messages
