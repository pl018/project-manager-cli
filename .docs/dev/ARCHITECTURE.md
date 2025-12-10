# Project Manager TUI - Architecture

## Overview
A beautiful terminal-based project manager with multi-tool integration, advanced search, tagging, and notes.

## Tech Stack
- **UI Framework**: Textual (modern Python TUI framework)
- **Database**: SQLite with enhanced schema
- **AI Integration**: OpenAI for smart tagging and descriptions
- **Tool Integration**: Multiple IDE/editor support

## Architecture

### Core Layer (`src/core/`)
- `database.py`: Enhanced SQLite manager with notes, tool configs
- `models.py`: Pydantic models for data validation
- `config.py`: Application configuration
- `exceptions.py`: Custom exception classes

### Integration Layer (`src/integrations/`)
- `base.py`: Base tool integration interface
- `cursor.py`: Cursor IDE integration
- `vscode.py`: VS Code integration
- `terminal.py`: Terminal/shell integration
- `jetbrains.py`: JetBrains IDEs (PyCharm, WebStorm, etc.)

### UI Layer (`src/ui/`)
- `app.py`: Main Textual application
- `screens/`:
  - `dashboard.py`: Main project browser
  - `project_detail.py`: Project detail view with notes
  - `search.py`: Advanced search interface
  - `settings.py`: Configuration screen
- `widgets/`:
  - `project_card.py`: Beautiful project card widget
  - `search_bar.py`: Search input with live filtering
  - `tag_editor.py`: Tag management widget
  - `notes_editor.py`: Rich text notes editor
  - `tool_selector.py`: Quick tool launcher

### CLI Layer (`src/cli/`)
- `main.py`: CLI entry point (backward compatible)
- `commands.py`: CLI commands for scripting

## Data Schema

### Enhanced Projects Table
```sql
CREATE TABLE projects (
    uuid TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    root_path TEXT NOT NULL UNIQUE,
    tags TEXT,  -- JSON array
    ai_app_name TEXT,
    ai_app_description TEXT,
    notes TEXT,  -- Rich text notes
    favorite INTEGER DEFAULT 0,
    last_opened TEXT,
    open_count INTEGER DEFAULT 0,
    date_added TEXT NOT NULL,
    last_updated TEXT NOT NULL,
    enabled INTEGER DEFAULT 1,
    color_theme TEXT DEFAULT 'blue'
);

CREATE TABLE tool_configs (
    project_uuid TEXT,
    tool_name TEXT,
    config TEXT,  -- JSON configuration
    FOREIGN KEY (project_uuid) REFERENCES projects(uuid)
);

CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    color TEXT DEFAULT '#3b82f6',
    icon TEXT DEFAULT '🏷️'
);
```

## UX Features

### Dashboard
- Grid/List view toggle
- Sort: Name, Date, Frequency, Favorites
- Filter: Tags, Tools, Favorites
- Quick actions: Open, Edit, Delete, Favorite

### Search
- Fuzzy text search
- Multi-tag filtering (AND/OR modes)
- Recent searches
- Saved filters

### Project Detail
- Full metadata display
- Notes editor with markdown preview
- Tag management
- Tool configuration
- Quick launch buttons

### Keyboard Shortcuts
- `j/k` or `↓/↑`: Navigate
- `/`: Focus search
- `Enter`: Open project detail
- `o`: Open in default tool
- `f`: Toggle favorite
- `n`: Add note
- `t`: Edit tags
- `q`: Quit/Back
- `?`: Help

## Tool Integration Protocol

Each tool integration implements:
```python
class ToolIntegration(ABC):
    @abstractmethod
    def is_available(self) -> bool:
        """Check if tool is installed/available"""

    @abstractmethod
    def open_project(self, path: str) -> bool:
        """Open project in this tool"""

    @abstractmethod
    def get_config_path(self) -> Optional[Path]:
        """Get tool's config file location"""
```

## Visual Design

### Color Scheme
- Primary: Blue (#3b82f6)
- Success: Green (#10b981)
- Warning: Yellow (#f59e0b)
- Error: Red (#ef4444)
- Accent: Purple (#8b5cf6)

### Components
- Cards with rounded borders
- Status indicators
- Progress bars for stats
- Color-coded tags
- Icons throughout (using Unicode)
