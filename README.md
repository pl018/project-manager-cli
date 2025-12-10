# Project Manager CLI

A powerful, cross-platform project management tool with both **CLI** and **TUI** (Terminal User Interface) modes. Manage your development projects, integrate with Cursor and other IDEs, and leverage AI-powered tagging for better organization.

![Python](https://img.shields.io/badge/python-3.12+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## Overview

Project Manager CLI provides two complementary interfaces:

- **CLI Mode** (`pm-cli`): Register and manage projects from the command line
- **TUI Mode** (`python main.py`): Browse, search, and manage projects with a beautiful terminal interface

Both modes share the same SQLite database, so your projects are synchronized across interfaces.

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
   ```

## Usage

### CLI Commands

```bash
# Initialize configuration
pm-cli init

# Register current directory as a project
pm-cli run

# Register with custom tag
pm-cli run --tag frontend

# Register specific directory
pm-cli run /path/to/project

# Test mode (no changes saved)
pm-cli run --test

# Skip AI tagging
pm-cli run --skip-ai-tags

# Show current configuration
pm-cli config

# Reset configuration
pm-cli reset
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
- **[TUI Documentation](.docs/user/README-TUI.md)** - TUI features and usage
- **[Troubleshooting](.docs/user/TROUBLESHOOTING.md)** - Common issues and solutions

### Developer Documentation

- **[Architecture](.docs/dev/ARCHITECTURE.md)** - System architecture and design
- **[Project Structure](.docs/dev/STRUCTURE.md)** - Code organization
- **[Migration Guide](.docs/dev/MIGRATION.md)** - Upgrading from v1.x

## Project Structure

```
project-manager-cli/
├── src/
│   ├── project_manager_cli/    # CLI application
│   │   ├── cli.py              # Click CLI commands
│   │   ├── app.py              # Application orchestration
│   │   ├── config.py            # Configuration management
│   │   └── services/           # Business logic services
│   ├── core/                   # Core functionality
│   │   ├── database.py         # SQLite database manager
│   │   ├── models.py           # Pydantic data models
│   │   └── config.py           # Core configuration
│   ├── integrations/           # IDE/tool integrations
│   │   ├── cursor.py           # Cursor integration
│   │   ├── vscode.py           # VS Code integration
│   │   ├── jetbrains.py        # JetBrains IDEs
│   │   └── registry.py         # Tool registry
│   └── ui/                     # TUI interface
│       ├── app.py              # Textual application
│       ├── screens/            # UI screens
│       └── widgets/            # UI components
├── main.py                     # TUI entry point
├── pyproject.py                # Legacy CLI entry point
└── pyproject.toml              # Package configuration
```

## Requirements

- Python 3.12+
- SQLite (included with Python)
- Optional: OpenAI API key for AI tagging

## Dependencies

- `click` - CLI framework
- `pydantic` - Data validation
- `textual` - TUI framework
- `rich` - Terminal formatting
- `pyyaml` - Configuration file parsing
- `openai` - AI tagging (optional)
- `python-dotenv` - Environment variable management

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

## Support

- **Issues**: Open an issue on GitHub
- **Documentation**: Check `.docs/` directory
- **TUI Help**: Press `?` in the TUI for keyboard shortcuts
- **CLI Help**: Run `pm-cli --help`

---

**Made with ❤️ for developers who love the terminal**
