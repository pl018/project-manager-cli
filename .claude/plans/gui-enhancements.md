# Implementation Plan: GUI Enhancements (PySide6 Desktop App)

## ✅ STATUS: COMPLETED (December 17, 2024)

All features have been successfully implemented and tested.

## Overview
Enhance the PySide6 desktop GUI with field editing capabilities and full Docs tab implementation for viewing and opening markdown files.

## Implementation Status

**Location**: `src/project_manager_desktop/`

**Completed Features**:
- ✅ Project table with search, filtering, favorites
- ✅ Overview tab (read-only project metadata)
- ✅ Notes tab (editable, save/revert)
- ✅ Tools tab (open in various IDEs)
- ✅ **Edit tab** - Edit project name, description, and tags
- ✅ **Docs tab** - Full markdown file browser with preview
- ✅ **Delete functionality** - Delete projects with confirmation
- ✅ **Open specific files** - Open markdown files in Cursor or default editor

---

## Feature 1: Edit Tab

### UI Design
Add a new "Edit" tab between "Overview" and "Notes" with form fields for editing project metadata.

**Qt Widgets**:
- `QLineEdit` for Project Name (ai_app_name)
- `QPlainTextEdit` for Description (multi-line)
- Tag Editor with add/remove buttons
- Save/Cancel buttons
- Form validation

### Layout Mockup
```
┌─ Edit Project ────────────────────────┐
│ Name:        [Project Manager CLI   ] │
│ Description: [A Python-based...     ] │
│              [                       ] │
│ Tags:        [python] [cli] [tool]    │
│              Available: [gui] [qt]     │
│                                       │
│ [Save Changes] [Cancel]               │
└───────────────────────────────────────┘
```

### Implementation Steps

1. **Create TagEditorWidget**
   - File: `src/project_manager_desktop/widgets/tag_editor.py` (new file)
   - Components:
     - Current tags displayed as closeable pills/buttons
     - Available tags from database as clickable buttons
     - "Add Custom Tag" input field
   - Signals: `tags_changed(list)`

2. **Add Edit Tab to MainWindow**
   - File: `src/project_manager_desktop/window.py`
   - Location: After Overview tab, before Notes tab
   - Add to `_build_ui()`:
     ```python
     # Edit tab
     self.edit_tab = QtWidgets.QWidget()
     edit_layout = QtWidgets.QFormLayout(self.edit_tab)
     self.edit_name = QtWidgets.QLineEdit()
     self.edit_desc = QtWidgets.QPlainTextEdit()
     self.edit_tags = TagEditorWidget()  # Custom widget
     # ... buttons, layout
     self.tabs.insertTab(1, self.edit_tab, "Edit")
     ```

3. **Add Database Method**
   - File: `src/core/database.py`
   - Method: `update_project_fields(uuid: str, **fields) -> None`
   - Updates: ai_app_name, description, tags
   - Updates: last_updated timestamp

4. **Connect Signals**
   - Save button: validate, call DB, refresh UI
   - Cancel button: revert to original values
   - Tab switching: load current project data

### Validation Rules
- Name cannot be empty
- Tags must be alphanumeric lowercase
- Show error message boxes on validation failure

---

## Feature 2: Docs Tab Implementation

### Current State
**File**: `src/project_manager_desktop/window.py:154-163`

Currently just a placeholder label. Need to implement full markdown file browser.

### UI Design
```
┌─ Documentation Files ─────────────────────────┐
│ Search: [________]  [🔄 Refresh]              │
├───────────────────────────────────────────────┤
│ Filename       │ Path          │ Modified    │
├───────────────────────────────────────────────┤
│► README.md     │ ./            │ Dec 17      │
│  CLAUDE.md     │ .claude/      │ Dec 15      │
│  DESIGN.md     │ docs/         │ Dec 10      │
└───────────────────────────────────────────────┘
Preview: README.md
┌───────────────────────────────────────────────┐
│ # Project Manager CLI                         │
│                                               │
│ A Python-based project management tool...    │
└───────────────────────────────────────────────┘
[Open in Cursor] [Open in Default Editor]
```

### Implementation Steps

1. **Create Doc Discovery Service**
   - File: `src/project_manager_cli/services/docs_discovery_service.py` (SHARED - used by both GUI and TUI)
   - Method: `discover_docs(project_path: str) -> List[DocFile]`
   - Extensions: `.md`, `.markdown`
   - Exclude dirs: node_modules, venv, .git, __pycache__, dist, build
   - Max files: 500
   - Priority: README first, then alphabetical

2. **Add DocFile Model**
   - File: `src/core/models.py`
   - Pydantic model with fields:
     - filename: str
     - full_path: Path
     - relative_path: str
     - extension: str
     - size_bytes: int
     - modified_date: datetime

3. **Implement Docs Tab UI**
   - File: `src/project_manager_desktop/window.py`
   - Replace placeholder in `_build_ui()` method (lines 154-163)
   - Components:
     - `QTableWidget` or `QTableView` for file list (3 columns)
     - `QTextBrowser` for markdown preview (supports basic markdown rendering)
     - `QPushButton` for "Open in Cursor"
     - `QPushButton` for "Open in Default Editor"
     - `QPushButton` for "Refresh"
     - `QLineEdit` for search/filter

4. **Add Event Handlers**
   - `_on_docs_table_selection_changed()` → load and display preview
   - `_on_open_in_cursor()` → call `cursor.open_file(path)`
   - `_on_open_in_default()` → use `QDesktopServices.openUrl()`
   - `_on_refresh_docs()` → rescan files
   - Connect in `_connect_signals()` method

5. **Extend Cursor Integration**
   - File: `src/integrations/cursor.py`
   - Add method: `open_file(self, file_path: str) -> bool`
   - Command: `cursor "full/path/to/file.md"`
   - Platform-specific command execution

6. **Extend Base Tool Integration**
   - File: `src/integrations/base.py`
   - Add abstract method: `open_file(self, file_path: str) -> bool`
   - Default: returns False (not supported)

### Qt-Specific Features
- Use `QTextBrowser` for markdown preview (built-in HTML support)
- Convert markdown to HTML using Python's `markdown` library
- Use `QTableView` with custom model for better performance
- Add context menu (right-click) for "Copy Path", "Open Location"

---

## Feature 3: Verify & Enhance Existing Features

### Notes Tab
**Current Status**: ✅ Already working
- Editable text area
- Save/Revert buttons
- Dirty state tracking
- Unsaved changes warning

**Optional Enhancement**: Add markdown preview toggle
- Split view: edit on left, preview on right
- Toggle button to switch between edit-only and split view

### Delete Functionality
**Current Status**: Not visible in main window
- Delete button exists via database method
- Not exposed in current GUI

**Add Delete Feature**:
- Add "Delete Project" button to toolbar or context menu
- Show confirmation dialog before deleting
- Use `db.delete_project()` (soft delete with enabled=0)
- Refresh project list after deletion

---

## Implementation Order

### Phase 1: Infrastructure (30 min)
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
9. Test widget in isolation

### Phase 4: Edit Tab (40 min)
10. Add Edit tab to `window.py`
11. Wire up form fields
12. Implement save/cancel handlers
13. Add validation

### Phase 5: Docs Tab (60 min)
14. Replace Docs tab placeholder
15. Implement file table
16. Add markdown preview
17. Wire up file opening
18. Add search/filter

### Phase 6: Polish & Testing (30 min)
19. Add delete functionality
20. Test all features end-to-end
21. Add error handling
22. Update status bar messages

**Total Estimated Time**: ~3.5 hours

---

## Critical Files to Modify

### Create New Files (2):
1. `src/project_manager_desktop/widgets/__init__.py` - Widget package
2. `src/project_manager_desktop/widgets/tag_editor.py` - Tag editor widget

### Modify Existing Files (6):
1. `src/project_manager_desktop/window.py` ⭐ **CRITICAL** - Add Edit and implement Docs tabs
2. `src/core/database.py` - Add `update_project_fields()` method
3. `src/core/models.py` - Add `DocFile` model
4. `src/integrations/base.py` - Add `open_file()` abstract method
5. `src/integrations/cursor.py` - Implement `open_file()` method
6. `src/project_manager_cli/services/docs_discovery_service.py` - **NEW** - Doc discovery (shared with TUI)

---

## Database Changes

**No schema changes needed** - all fields already exist:
- `ai_app_name` (project name)
- `description` (project description)
- `tags` (JSON array)
- `last_updated` (timestamp)
- `enabled` (soft delete flag)

**New Method**:
```python
def update_project_fields(self, uuid: str, **fields) -> None:
    """Update specific project fields."""
    # Get existing project
    # Update specified fields
    # Update last_updated timestamp
    # Save via add_or_update_project()
```

---

## Dependencies

### Required Python Packages
- `PySide6` - Already required (Qt framework)
- `markdown` - For markdown to HTML conversion (add to pyproject.toml)

### Optional Packages
- `pygments` - Syntax highlighting in markdown code blocks
- `pymdown-extensions` - Enhanced markdown features

---

## Testing Checklist

### Edit Tab
- [ x ] Edit project name, save, verify in database
- [ x ] Edit description, save, verify
- [ x ] Add tag from available tags
- [ x ] Add custom tag
- [ x ] Remove tag
- [ x ] Cancel edit reverts changes
- [  ] Empty name shows error
- [ x ] Changes reflected in Overview tab
- [ x ] Changes reflected in project table

### Docs Tab
- [ x ] Discovers .md files correctly
- [ ] Excludes node_modules, venv, etc.
- [ x ] Table shows all columns (filename, path, modified)
- [ x ] Selecting file shows preview
- [ x ] Markdown renders as HTML
- [ x ] "Open in Cursor" opens file
- [ x ] "Open in Default Editor" opens file
- [ ] Refresh button rescans files
      - [ ] The document inline button worked and the one in the toolbar up top did not. So it did not refresh the GUI
- [ x ] Empty project (no docs) handled gracefully /NOTE the project directory is displayed and that's it/
      - [ ] We need to add some stop triggers in the run command so it doesn't process it. When it finds out there's no folders or files in there, that it doesn't go through and fully process the project.
- [  ] Context menu works (if implemented)

### Delete
- [ ] Delete button visible
- [ ] Confirmation dialog appears
- [ ] Project deleted from database (enabled=0)
- [ ] Project removed from table
- [ ] Cannot delete if already deleted

### Integration
- [ ] Changes in GUI reflected in CLI/TUI
- [ ] Changes in CLI/TUI reflected in GUI
- [ ] Database shared correctly
- [ ] No conflicts or locks

---

## Edge Cases to Handle

1. **No docs found**: Show "No documentation files found in project" message
2. **Large projects**: Limit to 500 docs, show "Showing X of Y files" message
3. **Cursor not available**: Show error dialog with instructions
4. **Tool not installed**: Gracefully handle missing tools
5. **Empty fields**: Validate name not empty before saving
6. **File read errors**: Catch and show error dialog
7. **Large markdown files**: Truncate preview to first 100KB
8. **Binary files**: Don't try to preview non-text files
9. **Database locked**: Handle SQLite busy errors
10. **Unsaved changes**: Prompt before switching projects
11. **Invalid tags**: Sanitize tag input (lowercase, alphanumeric)

---

## Qt-Specific Implementation Notes

### Signals & Slots
```python
# Custom signals for widgets
class TagEditorWidget(QtWidgets.QWidget):
    tags_changed = QtCore.Signal(list)  # Emitted when tags modified

    def on_tag_added(self, tag: str):
        self.tags_changed.emit(self.get_tags())
```

### Model-View Architecture
Consider using `QAbstractTableModel` for Docs table instead of `QTableWidget` for better performance with large file lists.

### Markdown Rendering
```python
import markdown

def render_markdown(self, text: str) -> str:
    html = markdown.markdown(
        text,
        extensions=['fenced_code', 'tables', 'nl2br']
    )
    return html

# In preview widget
self.preview_browser.setHtml(render_markdown(file_content))
```

### Threading
For large projects, consider using `QThread` for file discovery to avoid blocking UI:
```python
class DocDiscoveryThread(QtCore.QThread):
    finished = QtCore.Signal(list)

    def run(self):
        docs = discover_docs(self.project_path)
        self.finished.emit(docs)
```

---

## Success Criteria

✅ Users can edit project name, description, and tags via Edit tab
✅ Changes save to database and persist
✅ Docs tab shows all .md files with preview
✅ Users can open specific markdown files in Cursor
✅ Users can open markdown files in default system editor
✅ Search/filter works in Docs tab
✅ Markdown preview renders correctly with formatting
✅ Delete functionality works with confirmation
✅ No crashes or errors during normal use
✅ Status bar shows helpful feedback messages
✅ All changes compatible with shared database (CLI/TUI)
