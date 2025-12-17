# Implementation Plan: TUI Enhancements (Textual Terminal UI)

## Overview
Enhance the Textual-based TUI with field editing, verify delete functionality, and implement a new Docs tab for viewing markdown files.

## User Requirements Confirmed
- **Field Editing**: Project Name, Description, Tags
- **UI Layout**: Tabbed interface (Overview/Edit/Docs)
- **File Opening**: Open specific file in Cursor (e.g., `cursor README.md`)
- **Doc Types**: `.md` and `.markdown` files only
- **Delete**: Already exists, verify it works

---

## Architecture: Tabbed Interface

Transform `ProjectDetailScreen` from single-view to tabbed layout:
```
┌─ Project Detail ────────────────────────┐
│ [Overview] [Edit] [Docs]                │
├─────────────────────────────────────────┤
│ (Tab content here)                      │
└─────────────────────────────────────────┘
```

---

## Feature 1: Edit Tab

### UI Design
- Input field for Project Name (ai_app_name)
- TextArea for Description (multi-line)
- Tag Editor with add/remove functionality
- Save/Cancel buttons
- Form validation

### Implementation Steps

1. **Create Tag Editor Widget**
   - File: `src/ui/widgets/tag_editor.py`
   - Show current tags as removable pills
   - Show available tags from database as clickable buttons
   - Messages: `TagAdded`, `TagRemoved`

2. **Create Edit Tab Widget**
   - File: `src/ui/widgets/edit_tab.py`
   - Extends `Static` (or `Container`)
   - Form fields: Input (name), TextArea (description), TagEditor (tags)
   - Save button: calls `db_manager.update_project_fields()`
   - Cancel button: resets fields to original values
   - Validation: name cannot be empty

3. **Add Database Method**
   - File: `src/core/database.py`
   - Method: `update_project_fields(uuid: str, **fields) -> None`
   - Updates specified fields: ai_app_name, description, tags
   - Updates `last_updated` timestamp
   - Uses existing `add_or_update_project()` internally

### Database Operations
```python
# Update project fields
db_manager.update_project_fields(
    project_uuid,
    ai_app_name="New Name",
    description="New Description",
    tags=["python", "cli"]
)
```

---

## Feature 2: Docs Tab

### UI Design
```
Documentation Files (12 found)

┌────────────────────────────────────────┐
│ Filename       Path          Modified │
├────────────────────────────────────────┤
│► README.md     ./            Dec 17   │
│  CLAUDE.md     ./.claude/    Dec 15   │
│  DESIGN.md     ./docs/       Dec 10   │
└────────────────────────────────────────┘

Preview: README.md
┌────────────────────────────────────────┐
│ # Project Manager CLI                  │
│                                        │
│ A Python-based project management...  │
└────────────────────────────────────────┘

[⚡ Open in Cursor] [🔄 Refresh]
```

### Implementation Steps

1. **Create Doc Discovery Service**
   - File: `src/project_manager_cli/services/docs_discovery_service.py` (SHARED with GUI)
   - Pattern: Similar to `ProjectContext.get_file_samples()`
   - Discovery method: `discover_docs(project_path: str) -> List[DocFile]`
   - File extensions: `.md`, `.markdown`
   - Exclude directories: node_modules, venv, .git, __pycache__, dist, build
   - Max files: 500 (configurable)
   - Sort: README first, then alphabetically

2. **Add DocFile Model**
   - File: `src/core/models.py`
   - Fields: filename, full_path, relative_path, extension, size_bytes, modified_date

3. **Create Docs Tab Widget**
   - File: `src/ui/widgets/docs_tab.py`
   - Extends `Static` (or `Container`)
   - Components:
     - `DataTable` for file list (3 columns: Filename, Path, Modified)
     - `Markdown` widget for preview (scrollable)
     - Buttons: "Open in Cursor", "Refresh"
   - State: selected_file, discovered_files
   - Events:
     - `on_data_table_row_selected()` → update preview
     - `on_button_pressed("open-in-cursor")` → open file in Cursor
     - `on_button_pressed("refresh-docs")` → rescan files

4. **Extend Cursor Integration for File Opening**
   - File: `src/integrations/cursor.py`
   - Add method: `open_file(self, file_path: str) -> bool`
   - Command: `cursor "path/to/file.md"` (opens specific file)
   - Windows: Use `wt` or `cmd` to run `cursor "file_path"`
   - macOS/Linux: Use `bash -c` to run `cursor "file_path"`

5. **Extend Base Tool Integration**
   - File: `src/integrations/base.py`
   - Add abstract method: `open_file(self, file_path: str) -> bool`
   - Default implementation: returns False (not supported)
   - Cursor overrides to support file opening

### File Discovery Pattern
```python
class DocsDiscoveryService:
    DOCS_EXTENSIONS = ['.md', '.markdown']
    EXCLUDE_DIRS = {
        'node_modules', 'venv', '.venv', 'env',
        'dist', 'build', '__pycache__', '.git'
    }

    def discover_docs(self, project_path: str) -> List[DocFile]:
        """Walk project directory, find markdown files."""
        # Use pathlib.Path.rglob('*.md')
        # Exclude unwanted directories
        # Prioritize README files
        # Limit to 500 files max
        # Return sorted list
```

---

## Feature 3: Project Detail Screen Refactor

### Transform to Tabbed Layout

**File**: `src/ui/screens/project_detail.py`

**Changes**:
1. Import: `from textual.widgets import TabbedContent, TabPane`
2. Refactor `compose()` method:
   ```python
   def compose(self) -> ComposeResult:
       yield Header()

       with TabbedContent(initial="overview"):
           with TabPane("Overview", id="overview"):
               # Move existing content here
               # (metadata, tool buttons, notes)

           with TabPane("Edit", id="edit"):
               yield EditTab(
                   project=self.project,
                   db_manager=self.db_manager
               )

           with TabPane("Docs", id="docs"):
               yield DocsTab(
                   project_path=self.project['root_path'],
                   tool_registry=self.tool_registry
               )

       yield Footer()
   ```

3. Update keyboard bindings:
   - Keep existing: `o`, `e`, `f`, `d`, `Esc`
   - Add (optional): `t` to cycle tabs, `1`/`2`/`3` to jump to tabs

4. Handle tab-specific events:
   - Listen for `EditTab.ProjectUpdated` → refresh overview
   - Listen for `DocsTab.FileOpened` → record open event

---

## Feature 4: Verify Delete Functionality

**Current Status**: Already implemented in `ProjectDetailScreen`
- Keyboard: `d` key
- Button: "🗑️ Delete"
- Method: `action_delete_project()`
- Database: `delete_project()` (soft delete, sets enabled=0)

**Verification Steps**:
1. Test delete keyboard shortcut
2. Test delete button
3. Confirm project disappears from dashboard
4. Confirm database record has `enabled=0`

**Optional Enhancement**: Add confirmation dialog
- Create `src/ui/widgets/confirm_dialog.py`
- Show "Are you sure?" modal before deleting
- Prevents accidental deletions

---

## Implementation Order

### Phase 1: Infrastructure (30 min)
1. Add `DocFile` model to `src/core/models.py`
2. Add `update_project_fields()` to `src/core/database.py`
3. Add `open_file()` to `src/integrations/base.py`
4. Implement `open_file()` in `src/integrations/cursor.py`

### Phase 2: Doc Discovery (20 min)
5. Create `src/project_manager_cli/services/docs_discovery_service.py`
6. Test doc discovery independently

### Phase 3: Widgets (40 min)
7. Create `src/ui/widgets/tag_editor.py`
8. Create `src/ui/widgets/edit_tab.py`
9. Create `src/ui/widgets/docs_tab.py`

### Phase 4: Integration (30 min)
10. Refactor `src/ui/screens/project_detail.py` with tabs
11. Add CSS styles to `src/ui/app.py`
12. Wire up event handlers

### Phase 5: Testing & Polish (20 min)
13. Test all features end-to-end
14. Verify delete functionality
15. Add error handling
16. Update keyboard shortcuts

**Total Estimated Time**: ~2.5 hours

---

## Critical Files to Modify

### Create New Files (5):
1. `src/ui/widgets/tag_editor.py` - Tag add/remove widget
2. `src/ui/widgets/edit_tab.py` - Edit form tab
3. `src/ui/widgets/docs_tab.py` - Docs browser tab
4. `src/project_manager_cli/services/docs_discovery_service.py` - File discovery (SHARED with GUI)
5. `src/ui/widgets/confirm_dialog.py` - Optional delete confirmation

### Modify Existing Files (5):
1. `src/ui/screens/project_detail.py` - Add tabbed interface ⭐ CRITICAL
2. `src/integrations/cursor.py` - Add `open_file()` method
3. `src/integrations/base.py` - Add `open_file()` abstract method
4. `src/core/database.py` - Add `update_project_fields()` method
5. `src/core/models.py` - Add `DocFile` model
6. `src/ui/app.py` - Add CSS for new widgets

---

## Database Changes

**No schema changes needed** - all fields already exist:
- `ai_app_name` (project name)
- `description` (project description)
- `tags` (JSON array)
- `last_updated` (timestamp)

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

## CSS Styling Notes

Add to `src/ui/app.py`:
- `.edit-tab` - Edit form container
- `.form-field` - Individual form fields
- `.tag-editor` - Tag editor container
- `.docs-tab` - Docs browser container
- `.docs-table` - DataTable styling
- `.docs-preview` - Markdown preview styling

---

## Testing Checklist

### Edit Tab
- [ ] Edit project name, save, verify in database
- [ ] Edit description, save, verify
- [ ] Add tag, save, verify
- [ ] Remove tag, save, verify
- [ ] Cancel edit, verify no changes
- [ ] Empty name validation

### Docs Tab
- [ ] Discovers .md files correctly
- [ ] Excludes node_modules, venv, etc.
- [ ] Table shows filename, path, date
- [ ] Selecting file shows preview
- [ ] Markdown renders correctly
- [ ] "Open in Cursor" opens file
- [ ] Refresh button rescans
- [ ] Empty project (no docs) handled

### Delete
- [ ] Keyboard `d` works
- [ ] Delete button works
- [ ] Project removed from dashboard
- [ ] Database `enabled=0`

### Navigation
- [ ] Tab switching works
- [ ] State preserved across tabs
- [ ] Keyboard shortcuts work
- [ ] Back button returns to dashboard

---

## Edge Cases to Handle

1. **No docs found**: Show "No documentation files found" message
2. **Large projects**: Limit to 500 docs, show count
3. **Cursor not available**: Show error, provide instructions
4. **Empty fields**: Validate name not empty before saving
5. **File read errors**: Catch and show error message
6. **Large markdown files**: Truncate preview to first 50KB

---

## Textual-Specific Implementation Notes

### Widget Composition
```python
class EditTab(Static):
    def compose(self) -> ComposeResult:
        yield Label("Project Name:")
        yield Input(id="name-input")
        yield Label("Description:")
        yield TextArea(id="desc-input")
        yield TagEditor(id="tag-editor")
        yield Button("Save", id="save-btn")
        yield Button("Cancel", id="cancel-btn")
```

### Message Handling
```python
class ProjectUpdated(Message):
    def __init__(self, project_uuid: str):
        self.project_uuid = project_uuid
        super().__init__()

# In EditTab
def on_button_pressed(self, event: Button.Pressed):
    if event.button.id == "save-btn":
        self.post_message(ProjectUpdated(self.project_uuid))
```

### DataTable Usage
```python
table = DataTable()
table.add_columns("Filename", "Path", "Modified")
for doc in docs:
    table.add_row(doc.filename, doc.relative_path, doc.modified_date)
```

---

## Success Criteria

✅ Users can edit project name, description, and tags
✅ Changes save to database and persist
✅ Docs tab shows all .md files in project
✅ Clicking doc opens specific file in Cursor
✅ Markdown preview renders correctly
✅ Delete functionality verified working
✅ Tabbed navigation smooth and intuitive
✅ No crashes or errors during normal use
✅ All keyboard shortcuts work as expected
✅ Compatible with shared database (CLI/GUI)
