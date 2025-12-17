# TUI Modernization Plan

## Overview
Modernize the Project Manager TUI with focus on fixing the notes bug, creating a clean minimal interface with compact project cards optimized for 120x30 terminal windows.

## User Requirements
- **Window Size**: Medium (120x30 typical)
- **Priorities**: Reliable notes editing, minimal clean interface
- **Visual Style**: Balanced (keep rounded borders/colors but simplify)
- **Card Layout**: Compact list (more projects visible)

## Root Cause: Notes Bug

**Location**: `src/ui/screens/project_detail.py:159-172`

**Problem**: Race condition in widget lifecycle during `refresh(layout=True)`:
1. `query_one("#notes-editor")` retrieves TextArea
2. `self.project['notes']` updated (line 166)
3. `refresh(layout=True)` called (line 169)
4. `compose()` rebuilds screen, destroying/recreating TextArea
5. If timing is off, UI shows stale content

**Solution**: Update state BEFORE refresh, ensure proper sequencing

---

## Implementation Phases

### Phase 1: Fix Notes Bug (CRITICAL)

**File**: `src/ui/screens/project_detail.py`

**Changes**:

1. **Lines 159-173**: Refactor `save_notes()` method
```python
def save_notes(self) -> None:
    """Save edited notes with proper state management."""
    try:
        # Capture text BEFORE any state changes
        editor = self.query_one("#notes-editor", TextArea)
        new_notes = editor.text

        # Update database
        self.db_manager.update_notes(self.project['uuid'], new_notes)

        # Update local state BEFORE refresh
        self.project['notes'] = new_notes

        # Exit edit mode
        self.edit_mode = False

        # Notify BEFORE refresh
        self.notify("Notes saved successfully", severity="information")

        # Refresh UI - compose() will use updated state
        self.refresh(layout=True)

    except Exception as e:
        self.notify(f"Error saving notes: {e}", severity="error")
```

2. **Lines 141-152**: Fix `action_toggle_favorite()` same pattern
```python
def action_toggle_favorite(self) -> None:
    """Toggle favorite status."""
    try:
        is_favorite = self.db_manager.toggle_favorite(self.project['uuid'])

        # Update state BEFORE refresh
        self.project['favorite'] = 1 if is_favorite else 0

        status = "added to" if is_favorite else "removed from"
        self.notify(f"Project {status} favorites", severity="information")

        # Refresh after state update
        self.refresh(layout=True)
    except Exception as e:
        self.notify(f"Error toggling favorite: {e}", severity="error")
```

3. **After line 157**: Add auto-focus helper
```python
def action_edit_notes(self) -> None:
    """Enter notes edit mode."""
    self.edit_mode = True
    self.refresh(layout=True)
    self.set_timer(0.1, self._focus_editor)

def _focus_editor(self) -> None:
    """Focus notes editor after layout."""
    try:
        editor = self.query_one("#notes-editor", TextArea)
        editor.focus()
    except Exception:
        pass
```

---

### Phase 2: Compact Project Cards

**File**: `src/ui/widgets/project_card.py`

**Replace**: Lines 27-78 (entire `compose()` method)

**New Implementation**:
```python
def compose(self) -> ComposeResult:
    """Create compact 2-line project card."""
    with Container(classes="project-card-compact"):
        # LINE 1: Name + stats
        name = self.project.get('name') or 'Unknown'
        favorite = self.project.get('favorite', 0)
        open_count = self.project.get('open_count', 0)
        last_opened = self.project.get('last_opened')

        fav_icon = "⭐ " if favorite else ""
        stats = ""
        if last_opened:
            try:
                dt = datetime.fromisoformat(last_opened)
                time_ago = self._time_ago(dt)
                stats = f" · {time_ago}"
            except:
                pass
        if open_count:
            stats += f" · ×{open_count}"

        name_line = f"{fav_icon}{name}{stats}"
        yield Label(name_line, classes="project-name-compact")

        # LINE 2: Path + tags
        path = self.project.get('root_path') or ''
        tags = self.project.get('tags') or []

        # Smart truncation for 120 cols
        max_path = 80 - (len(tags) * 8 if tags else 0)
        if len(path) > max_path:
            path = "..." + path[-(max_path-3):]

        tag_badges = " ".join([f"[{t}]" for t in tags[:3]])
        path_line = f"📁 {path}  {tag_badges}" if tag_badges else f"📁 {path}"

        yield Label(path_line, classes="project-path-compact")
```

**Result**: 2-line cards (vs 8-12 lines) → show 15-20 projects instead of 5-8

---

### Phase 3: Minimal Interface Updates

**File**: `src/ui/screens/dashboard.py`

**Changes**:

1. **Lines 37-65**: Simplify top bar to single line
```python
with Horizontal(id="top-bar-compact"):
    yield Label("", id="stats-compact")
    yield Button("⭐", id="fav-btn", variant="primary")
    yield Button("🔄", id="refresh-btn")
```

2. **Integrate search**: Move search into top bar (remove separate container)

3. **Collapsible tag filter**: Hide by default, toggle with 't' key
```python
with Container(id="tag-filter-compact", classes="hidden"):
    # Tag filter content
```

4. **Lines 17-25**: Add keyboard bindings
```python
BINDINGS = [
    # ... existing
    Binding("t", "toggle_tags", "Tags", show=True),
    Binding("j", "focus_next", "Down", show=False),
    Binding("k", "focus_previous", "Up", show=False),
]
```

5. **Add action methods**:
```python
def action_toggle_tags(self) -> None:
    """Toggle tag filter visibility."""
    container = self.query_one("#tag-filter-compact")
    container.toggle_class("hidden")

def action_focus_next(self) -> None:
    """Vim j navigation."""
    self.screen.focus_next()

def action_focus_previous(self) -> None:
    """Vim k navigation."""
    self.screen.focus_previous()
```

**File**: `src/ui/screens/project_detail.py`

**Lines 42-63**: Simplify metadata display
```python
with Container(id="metadata-compact"):
    path = self.project.get('root_path', '')
    yield Label(f"📁 {path}", classes="meta-line")

    tags = self.project.get('tags', [])
    if tags:
        yield Label(f"🏷️  {' '.join(tags)}", classes="meta-line")
```

**Lines 66-78**: Compact action buttons
```python
with Horizontal(id="actions-compact"):
    yield Button("Open", id="open-default", variant="primary")
    yield Button("⭐", id="fav-btn", variant="warning")
    yield Button("Delete", id="del-btn", variant="error")
```

---

### Phase 4: CSS Simplification

**File**: `src/ui/app.py`

**Remove/Reduce** (lines 15-265):
- Top bar height: 3 → 1 (line 39)
- Remove separate search container (lines 64-67)
- Simplify tag filter (lines 92-103)
- Remove verbose card styles (lines 140-189)
- Reduce metadata padding (lines 198-219)

**Add Compact Styles** (after line 265):
```css
/* Compact Top Bar */
#top-bar-compact {
    height: 1;
    padding: 0 1;
    background: $panel;
}

/* Compact Project Cards */
.project-card-compact {
    height: 3;
    margin-bottom: 1;
    padding: 0 2;
    background: $panel;
    border-left: thick $primary;
}

.project-card-compact:hover {
    background: $surface;
    border-left: thick $accent;
}

.project-card-compact:focus {
    background: $surface;
    border-left: thick $success;
}

.project-name-compact {
    text-style: bold;
    color: $accent;
}

.project-path-compact {
    color: $text-muted;
}

/* Compact Metadata */
#metadata-compact {
    padding: 1;
    margin-bottom: 1;
}

.meta-line {
    margin-bottom: 0;
}

/* Compact Actions */
#actions-compact {
    height: 3;
    margin-bottom: 1;
}

/* Responsive Notes Editor */
#notes-editor {
    height: 1fr;
    min-height: 10;
    max-height: 20;
}

/* Collapsible Tag Filter */
#tag-filter-compact.hidden {
    display: none;
}
```

**Keep** (for balanced visual style):
- Rounded borders
- Color scheme (primary, accent, success, etc.)
- Hover/focus states
- Text formatting

---

## Testing Checklist

### Notes Bug Verification
- [ ] Edit notes and save → verify immediate display
- [ ] Navigate away and back → verify persistence
- [ ] Edit and cancel → verify no changes
- [ ] Test with empty notes, multiline, special chars
- [ ] Test rapid save/edit cycles

### Compact Layout (120x30 window)
- [ ] Verify 15-20 projects visible on dashboard
- [ ] Check path truncation on long paths (>80 chars)
- [ ] Verify max 3 tags displayed per card
- [ ] Check favorite icon alignment
- [ ] Test with 0, 1, and 100+ projects

### Navigation
- [ ] Test vim j/k between cards
- [ ] Test '/' to focus search
- [ ] Test 't' to toggle tag filter
- [ ] Test Esc to clear filters
- [ ] Test tab/shift+tab focus

### Visual Polish
- [ ] Verify rounded borders present
- [ ] Check hover states work
- [ ] Verify focus indicators visible
- [ ] Check color consistency
- [ ] Test in different terminal themes

---

## Critical Files

- `C:\Users\chris\.myAiBS\system-tools\project-manager-cli\src\ui\screens\project_detail.py`
  - Lines 141-177: Notes bug fix, favorite fix

- `C:\Users\chris\.myAiBS\system-tools\project-manager-cli\src\ui\widgets\project_card.py`
  - Lines 27-78: Replace with compact 2-line layout

- `C:\Users\chris\.myAiBS\system-tools\project-manager-cli\src\ui\app.py`
  - Lines 15-265: CSS refactoring + new compact styles

- `C:\Users\chris\.myAiBS\system-tools\project-manager-cli\src\ui\screens\dashboard.py`
  - Lines 17-25: Add vim navigation bindings
  - Lines 37-65: Simplify top bar
  - Add toggle_tags, focus_next/previous methods

---

## Implementation Order

1. **Phase 1**: Notes bug fix (30 min) - Critical, isolated change
2. **Phase 2**: Compact cards (45 min) - Foundation for new layout
3. **Phase 4**: CSS updates (1 hour) - Enable responsive design
4. **Phase 3**: Interface simplification (45 min) - Polish and integrate
5. **Testing**: Comprehensive validation (1 hour)

**Total Estimate**: 4-5 hours

---

## Success Criteria

✅ Notes editing works reliably (save, persist, cancel)
✅ 15-20 projects visible in 120x30 window (vs 5-8 currently)
✅ Clean, minimal interface with balanced visual style
✅ Rounded borders and color scheme maintained
✅ Smooth keyboard navigation (vim keys, shortcuts)
✅ No regressions in existing functionality
