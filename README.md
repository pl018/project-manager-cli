# Project Manager CLI

A powerful, cross-platform project management tool with **three** complementary interfaces. Manage your development projects, integrate with Cursor and other IDEs, and leverage AI-powered tagging for better organization.

![Python](https://img.shields.io/badge/python-3.12+-green)
![License](https://img.shields.io/badge/license-MIT-orange)
![Status](https://img.shields.io/badge/status-active_development-blue)

## Overview

Project Manager CLI provides three interfaces for managing your projects:

- **CLI Mode** (`pm-cli`): Register and manage projects from the command line with rich formatting
- **TUI Mode** (`python main.py` or `pm-cli tui`): Browse, search, and manage projects with a beautiful terminal interface built with Textual
- **GUI Mode** (`pm-gui`): Desktop GUI built with PySide6 (Qt) for graphical project management with advanced features

All three modes share the same SQLite database, so your projects are synchronized across interfaces.

## Features

### Core Capabilities

- **Stable Project Identity**: Each project gets a unique UUID stored in `.pyprojectid`
- **SQLite Backend**: Robust database prevents duplicates and enables reliable updates
- **Cursor Integration**: Auto-generates `projects.json` for Cursor Project Manager extension
- **Multi-Tool Support**: Open projects in Cursor, VS Code, PyCharm, WebStorm, IntelliJ, Terminal, and more
- **AI-Powered Tagging**: Optional OpenAI integration for intelligent project tagging and descriptions
- **Rich Notes**: Add markdown notes to projects for documentation
- **Search & Filter**: Powerful search across names, paths, tags, and notes
- **Usage Tracking**: Track how often you open projects and when they were last accessed

### CLI Mode Features

- Single command registration: `pm-cli run`
- Custom tags: `pm-cli run --tag frontend`
- Test mode: `pm-cli run --test` (dry-run without changes)
- Per-project logging with detailed receipts
- Configuration management: `pm-cli init`, `pm-cli config`, `pm-cli reset`

### TUI Mode Features

- Beautiful terminal interface built with Textual
- Real-time search and filtering
- Project cards with visual metadata
- Tag filtering with color-coded tags
- Favorites system
- Keyboard shortcuts (vim-style navigation)
- Mouse support
- Project statistics and usage tracking

### GUI Mode Features

- **Desktop GUI** built with PySide6 (Qt6)
- **Multi-tab Interface**:
  - **Overview Tab**: Project details, statistics, and quick actions
  - **Notes Tab**: Rich markdown notes editor with preview
  - **Edit Tab**: Edit project name, description, and tags with validation
  - **Tools Tab**: Configure and launch external tools (Cursor, VS Code, etc.)
  - **Docs Tab**: Browse and preview markdown files in your project
- **Advanced Features**:
  - **Archive Projects**: Backup projects to ZIP with automatic cleanup of library folders (node_modules, venv, etc.)
  - **Git Integration**: Detect uncommitted changes before archiving
  - **Hard Delete**: Permanently remove projects from database
  - **Directory Cleanup**: Delete project files from disk with powerful force-deletion
  - **Filter by Status**: Show/hide archived projects
- **Dark Theme**: Nord-inspired color scheme with excellent readability
- **Table View**: Sortable, filterable table of all projects
- **Search & Filter**: Real-time filtering by name, path, tags, and favorites

## Quick Start

### Installation

1. **Install the package** (development mode):
   ```bash
   pip install -e .
   ```
   
   Or using UV (recommended):
   ```bash
   uv pip install -e .
   ```

2. **Initialize configuration**:
   ```bash
   pm-cli init
   ```
   
   This will prompt you for:
   - Database location (defaults provided)
   - Cursor `projects.json` path
   - Optional OpenAI API key for AI tagging

3. **Register your first project**:
   ```bash
   cd /path/to/your/project
   pm-cli run
   ```

4. **Launch the TUI** to browse your projects:
   ```bash
   python main.py
   # OR
   pm-cli tui
   ```

5. **Launch the GUI** (optional, requires PySide6):
   ```bash
   pm-gui
   ```

## Usage

### CLI Commands

#### Windows Explorer right-click (Context Menu)

On Windows, you can add a folder right-click menu item that opens a new PowerShell window, runs `pm-cli run` on that folder, then waits for a keypress before closing.

```bash
# Install (no admin required)
pm-cli context-menu install

# Verify
pm-cli context-menu status

# Remove
pm-cli context-menu uninstall
```

#### Initialize Configuration

```bash
# Interactive setup (recommended for first time)
pm-cli init

# Set all options at once
pm-cli init --db-path ~/.myaibs/projects.db \
            --projects-file ~/AppData/Roaming/Cursor/User/globalStorage/projects.json \
            --openai-api-key sk-...

# Force reconfiguration
pm-cli init --force

# Set only database path (will prompt for others)
pm-cli init --db-path ~/my-projects.db
```

#### Run Project Registration

```bash
# Register current directory as a project
pm-cli run

# Register specific directory
pm-cli run /path/to/project

# Test mode (analyze without saving changes)
pm-cli run --test

# Test specific project
pm-cli run --test ~/projects/my-app
```

#### List Projects

```bash
# List all projects
pm-cli list

# List only favorite projects
pm-cli list --favorites
pm-cli list -f

# Filter by single tag
pm-cli list --tag python
pm-cli list -t python

# Filter by multiple tags (AND logic)
pm-cli list --tag python --tag web
pm-cli list -t python -t web

# Search by name or path
pm-cli list --search "my-app"
pm-cli list -s backend

# Combine filters
pm-cli list --favorites --tag python --search "api"
pm-cli list -f -t python -s api
```

#### Generate HTML Report

```bash
# Generate and open HTML in browser
pm-cli html

# Generate without opening browser
pm-cli html --no-open

# Save to specific location
pm-cli html --output ~/projects.html
pm-cli html -o ~/Desktop/my-projects.html

# Generate to file without opening
pm-cli html --output report.html --no-open
```

#### Configuration Management

```bash
# Show current configuration
pm-cli config

# Reset configuration (will prompt for confirmation)
pm-cli reset
```

#### Launch Interactive TUI

```bash
# Launch interactive terminal UI
pm-cli tui
```

### TUI Navigation

**Keyboard Shortcuts:**
- `j` / `↓` - Move down
- `k` / `↑` - Move up
- `/` - Focus search bar
- `Enter` - Open project details
- `o` - Open project in default tool
- `f` - Toggle favorite
- `q` - Quit
- `?` - Show help

**Mouse Support:**
- Click project cards to view details
- Click tags to filter
- Click buttons to execute actions

### GUI Navigation

The GUI provides a full desktop experience with:

**Main Window:**
- **Projects Table**: View all projects with sortable columns (Name, Path, Tags, Last Opened)
- **Search Bar**: Filter projects by name, path, or tags
- **Toolbar Buttons**:
  - "Show Favorites" - Filter to favorite projects only
  - "Show Archived" - Toggle archived projects visibility
  - "Refresh" - Reload project list
  - "Open in Tool" - Launch selected project in configured tool
  - "Archive" - Backup project with cleanup options
  - "Delete" - Remove project (soft or hard delete)

**Project Detail Tabs:**
- **Overview**: View project metadata, statistics, and quick actions
- **Notes**: Edit rich markdown notes with live preview
- **Edit**: Modify project name, description, and tags
- **Tools**: Configure which tool to use (Cursor, VS Code, PyCharm, etc.)
- **Docs**: Browse markdown documentation in your project

## Configuration

### Configuration File

Location:
- **Windows**: `%APPDATA%\project-manager-cli\config.yaml`
- **Linux/macOS**: `~/.config/project-manager-cli/config.yaml`

### Environment Variables

Override configuration with environment variables:

```bash
# Database path
export PROJECT_MANAGER_DB_PATH="/custom/path/to/database.db"

# Cursor projects.json path
export PROJECT_MANAGER_PROJECTS_FILE="/custom/path/to/projects.json"

# OpenAI API key (for AI tagging)
export OPENAI_API_KEY="sk-..."
```

### AI Tagging

Set `OPENAI_API_KEY` in your environment or config file to enable AI enrichment. The CLI will:
- Sample files from your project
- Generate intelligent tags (2-3 tags, one-word lowercase alphanumeric)
- Infer app name and description
- Disable with `--skip-ai-tags` flag

## Data Storage

### Database Location

- **Windows**: `%APPDATA%\project-manager-cli\project_manager_data.db`
- **Linux/macOS**: `~/.config/project-manager-cli/project_manager_data.db`

### Project Files

- **UUID File**: `<project-root>/.pyprojectid` - Contains stable project UUID
- **Cursor Projects**: `%APPDATA%\Cursor\User\globalStorage\alefragnani.project-manager\projects.json` (auto-generated)

### Logs

Per-project logs are stored at:
- **Windows**: `%APPDATA%\project-manager-cli\logs\<uuid>.log`
- **Linux/macOS**: `~/.config/project-manager-cli/logs/<uuid>.log`

## Documentation

### User Documentation

- **[Installation Guide](.docs/user/INSTALL.md)** - Detailed installation instructions
- **[Usage Guide](.docs/user/USAGE.md)** - Complete command reference
- **[Configuration Guide](.docs/user/CONFIGURATION.md)** - Configuration options
- **[Quick Start Guide](.docs/user/QUICKSTART.md)** - 5-minute setup guide
- **[Troubleshooting](.docs/user/TROUBLESHOOTING.md)** - Common issues and solutions

### Developer Documentation

- **[Architecture](.docs/dev/ARCHITECTURE.md)** - System architecture and design
- **[Project Structure](.docs/dev/STRUCTURE.md)** - Code organization
- **[Migration Guide](.docs/dev/MIGRATION.md)** - Upgrading from v1.x

## Project Structure

```
project-manager-cli/
├── src/
│   ├── project_manager_cli/      # CLI application layer
│   │   ├── cli.py                # Click CLI commands
│   │   ├── app.py                # Application orchestration
│   │   ├── services/             # Business logic services
│   │   │   ├── ai_service.py             # OpenAI integration
│   │   │   ├── archive_service.py        # Archive operations
│   │   │   ├── git_service.py            # Git utilities
│   │   │   ├── docs_discovery_service.py # Markdown file discovery
│   │   │   └── ...
│   │   └── formatters/           # Output formatting (HTML, tables)
│   ├── core/                     # Core domain layer (SHARED)
│   │   ├── database.py           # DatabaseManager with schema
│   │   ├── models.py             # Pydantic data models
│   │   ├── config.py             # Static configuration
│   │   ├── config_manager.py     # Dynamic YAML config
│   │   └── exceptions.py         # Custom exceptions
│   ├── integrations/             # IDE/tool integration layer
│   │   ├── base.py               # ToolIntegration abstract base
│   │   ├── cursor.py             # Cursor IDE integration
│   │   ├── vscode.py             # VS Code integration
│   │   ├── jetbrains.py          # PyCharm, WebStorm, IntelliJ
│   │   ├── terminal.py           # Terminal/shell integration
│   │   ├── explorer.py           # File explorer integration
│   │   └── registry.py           # Tool registry/factory
│   ├── ui/                       # TUI presentation layer (Textual)
│   │   ├── app.py                # ProjectManagerApp main application
│   │   ├── screens/              # TUI screens
│   │   │   ├── dashboard.py          # Main project browser
│   │   │   └── project_detail.py     # Project detail view
│   │   └── widgets/              # TUI components
│   │       ├── project_card.py       # Project card component
│   │       ├── search_bar.py         # Search input widget
│   │       └── tag_pill.py           # Tag display widget
│   └── project_manager_desktop/  # GUI presentation layer (PySide6)
│       ├── main.py               # Entry point for GUI (pm-gui)
│       ├── window.py             # MainWindow with tabs
│       ├── models.py             # Qt models (ProjectsTableModel, FilterProxyModel)
│       ├── theme.py              # Nord-inspired dark theme
│       ├── dialogs/              # Dialog widgets
│       │   └── archive_dialog.py     # Archive project dialog
│       └── widgets/              # GUI widgets
│           └── tag_editor.py         # Tag editor with flow layout
├── main.py                       # TUI entry point
├── pyproject.py                  # Legacy CLI entry point (backward compatibility)
└── pyproject.toml                # Package configuration
```

## Requirements

- Python 3.12+
- SQLite (included with Python)
- Optional: OpenAI API key for AI tagging

## Dependencies

### Core Dependencies
- `click` - CLI framework
- `pydantic` - Data validation
- `rich` - Terminal formatting
- `pyyaml` - Configuration file parsing
- `python-dotenv` - Environment variable management

### TUI Dependencies
- `textual` - TUI framework for terminal interface

### GUI Dependencies (Optional)
- `PySide6` - Qt6 bindings for desktop GUI
- `markdown` - Markdown rendering
- `pygments` - Syntax highlighting
- `pymdown-extensions` - Enhanced markdown features

### Optional Dependencies
- `openai` - AI-powered tagging (requires API key)

## Backward Compatibility

The application maintains backward compatibility:

- Legacy `pyproject.py` script still works
- Existing `.pyprojectid` files are recognized
- Database schema is backward compatible
- Cursor integration unchanged

## Contributing

Contributions are welcome! Please:

1. Check existing issues and documentation
2. Follow the code style (use `black` for formatting)
3. Add tests for new features
4. Update documentation as needed

## License

MIT License - See LICENSE file for details

## Getting Help

### CLI Help

```bash
# Show main help with all commands
pm-cli --help

# Show detailed help for specific command
pm-cli init --help
pm-cli run --help
pm-cli list --help
pm-cli html --help
pm-cli config --help
pm-cli reset --help
pm-cli tui --help
```

Each command includes:
- Detailed description
- All available options and flags
- Real-world usage examples
- Short and long option formats

### TUI Help

Press `?` in the TUI for a complete list of keyboard shortcuts and features.

## Support

- **Issues**: Open an issue on GitHub
- **Documentation**: Check `.docs/` directory
- **TUI Help**: Press `?` in the TUI for keyboard shortcuts
- **CLI Help**: Run `pm-cli --help` or `pm-cli COMMAND --help`

---

**Made with ❤️ for developers who love the terminal**
