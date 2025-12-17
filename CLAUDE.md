# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Project Manager CLI is a Python-based cross-platform project management tool with dual interfaces:
- **CLI Mode** (`pm-cli`): Command-line interface for registering and managing projects
- **TUI Mode** (`python main.py`): Terminal User Interface built with Textual for browsing and managing projects

Both modes share a SQLite database backend and support Cursor IDE integration, AI-powered tagging via OpenAI, and multi-tool support (VS Code, PyCharm, WebStorm, etc.).

## Key Commands

### Development Setup
```bash
# Install dependencies (development mode)
pip install -e .
# Or using UV (recommended)
uv pip install -e .

# Initialize configuration
pm-cli init
```

### CLI Commands
```bash
# Register a project
pm-cli run [path]
pm-cli run --test  # Dry-run mode

# List projects
pm-cli list
pm-cli list --favorites
pm-cli list --tag python --search "api"

# Generate HTML report
pm-cli html --output report.html

# View configuration
pm-cli config

# Launch TUI
pm-cli tui
```

### TUI Launch
```bash
# Launch interactive TUI
python main.py
```

### Testing and Development
There is no formal test suite currently in this project. When adding tests:
- Follow Python pytest conventions
- Create `tests/` directory structure
- Test database operations, CLI commands, and TUI components separately

## Architecture

### High-Level Structure

The codebase uses a **modular layered architecture** with clear separation of concerns:

```
src/
├── project_manager_cli/   # CLI application layer
│   ├── cli.py             # Click commands (init, run, list, html, config, reset, tui)
│   ├── app.py             # Application orchestrator
│   ├── config.py          # Configuration management
│   ├── services/          # Business logic layer
│   │   ├── ai_service.py          # OpenAI integration
│   │   ├── database_service.py    # SQLite operations
│   │   ├── project_service.py     # Project info collection
│   │   └── project_manager_service.py  # Cursor integration
│   └── formatters/        # Output formatting (HTML, tables)
├── core/                  # Core domain layer (shared by CLI and TUI)
│   ├── database.py        # DatabaseManager with enhanced schema
│   ├── models.py          # Pydantic models (Project, Tag, ToolConfig)
│   ├── config.py          # Core configuration
│   └── exceptions.py      # Custom exceptions
├── integrations/          # IDE/tool integration layer
│   ├── base.py           # ToolIntegration abstract base class
│   ├── cursor.py         # Cursor IDE integration
│   ├── vscode.py         # VS Code integration
│   ├── jetbrains.py      # PyCharm, WebStorm, IntelliJ
│   ├── terminal.py       # Terminal/shell integration
│   └── registry.py       # Tool registry/factory
└── ui/                   # TUI presentation layer (Textual)
    ├── app.py            # ProjectManagerApp main application
    ├── screens/
    │   ├── dashboard.py       # Main project browser
    │   └── project_detail.py  # Project detail view
    └── widgets/
        ├── project_card.py    # Project card component
        ├── search_bar.py      # Search input widget
        └── tag_pill.py        # Tag display widget
```

### Data Flow

1. **CLI Commands** → `cli.py` (Click) → `app.py` (Application) → Services → Core Database
2. **TUI** → `main.py` → `ui/app.py` (Textual) → Core Database → Integrations
3. **Project Registration** → Services collect metadata → AI tagging (optional) → Database → Cursor integration

### Database Schema

SQLite database with three main tables:

**projects table:**
- UUID (primary key, stored in `.pyprojectid` files)
- name, root_path (unique)
- tags (JSON array), ai_app_name, ai_app_description
- notes (markdown text)
- favorite, last_opened, open_count (usage tracking)
- date_added, last_updated
- enabled, color_theme

**tags table:**
- Global tag registry with color and icon metadata

**tool_configs table:**
- Per-project tool configurations (JSON)

### Entry Points

- `pm-cli` command: `src/project_manager_cli/cli.py:main()` (defined in pyproject.toml)
- TUI: `main.py` → `src/ui/app.py:run_tui()`
- Legacy: `pyproject.py` (backward compatibility wrapper)

## Important Implementation Details

### Configuration System

Two-tier configuration:
1. **ConfigManager** (CLI layer): Handles user config file in `%APPDATA%/project-manager-cli/config.yaml` (Windows) or `~/.config/project-manager-cli/config.yaml` (Linux/macOS)
2. **Config** (Core layer): Application-wide constants and defaults

Environment variables override config file settings:
- `PROJECT_MANAGER_DB_PATH`
- `PROJECT_MANAGER_PROJECTS_FILE`
- `OPENAI_API_KEY`

### Project Identity

Each project gets a stable UUID stored in `<project-root>/.pyprojectid`:
- UUID is generated once and persists across registrations
- Allows detecting if a project is already registered
- Prevents duplicate entries in database
- Used as the foreign key for tool_configs

### Cursor Integration

Auto-generates Cursor Project Manager extension's `projects.json`:
- Located at `%APPDATA%\Cursor\User\globalStorage\alefragnani.project-manager\projects.json`
- Format: Array of `{name, rootPath, paths: []}` objects
- Regenerated on every project registration
- Maintains backward compatibility with existing Cursor users

### AI Tagging Service

OpenAI integration for intelligent project metadata:
- Samples files from project (up to 30 files, various types)
- Generates 2-3 tags (one-word lowercase alphanumeric)
- Infers app name and description
- Respects `.gitignore` patterns
- Can be disabled with `--skip-ai-tags` flag
- Requires `OPENAI_API_KEY` environment variable

### Tool Integration Protocol

All tool integrations implement `ToolIntegration` abstract base class:
```python
class ToolIntegration(ABC):
    def is_available() -> bool
    def open_project(path: str) -> bool
    def get_config_path() -> Optional[Path]
```

Tools are registered in `integrations/registry.py` and can be extended by adding new integration modules.

### TUI Implementation

Built with Textual framework:
- App class: `ProjectManagerApp` extends `textual.app.App`
- Screens: Dashboard (main), ProjectDetail (details view)
- Widgets: ProjectCard (Textual Container), SearchBar (Input wrapper), TagPill (Static label)
- Keyboard shortcuts: vim-style navigation (j/k), `/` for search, `o` to open, `f` to favorite
- Reactive properties for real-time updates

### Rich CLI Output

Uses Rich library for formatted CLI output:
- Custom `RichGroup` and `RichCommand` classes for Click commands
- Tables for project listings (`formatters/table_formatter.py`)
- HTML generation for reports (`formatters/html_generator.py`)
- Safe emoji handling for Windows compatibility

## Cross-Platform Considerations

- **Path handling**: Use `pathlib.Path` consistently
- **Database location**: Platform-specific defaults via `Config.get_default_db_path()`
- **Emoji support**: `safe_emoji()` function in `cli.py` for Windows compatibility
- **Cursor paths**: Windows-specific paths in `integrations/cursor.py`

## Configuration Files

### User Configuration
- Location: `%APPDATA%\project-manager-cli\config.yaml` (Windows) or `~/.config/project-manager-cli/config.yaml` (Linux/macOS)
- Format: YAML with `database_path`, `projects_file`, `openai_api_key`

### Project Metadata
- `.pyprojectid`: Contains single-line UUID for project identity
- Per-project logs: `%APPDATA%\project-manager-cli\logs\<uuid>.log`

### Python Package
- `pyproject.toml`: Standard Python package configuration with Hatchling build backend
- Minimum Python: 3.12+
- Entry points: `project-manager-cli` and `pm-cli` (aliases)

## Common Development Patterns

### Adding a New CLI Command
1. Add command function in `src/project_manager_cli/cli.py` with `@cli.command()` decorator
2. Use `RichCommand` class for rich help text
3. Include detailed docstring with examples
4. Use `console.print()` for formatted output

### Adding a New Tool Integration
1. Create new file in `src/integrations/` (e.g., `neovim.py`)
2. Extend `ToolIntegration` abstract base class from `base.py`
3. Implement `is_available()`, `open_project()`, `get_config_path()`
4. Register in `registry.py` via `ToolRegistry.register()`

### Adding a New TUI Screen
1. Create new screen class in `src/ui/screens/` extending `textual.screen.Screen`
2. Define CSS styles inline or in `app.py`
3. Implement `compose()` method for layout
4. Add keyboard bindings with `BINDINGS` class attribute
5. Push screen in app with `self.app.push_screen(NewScreen())`

### Extending the Database Schema
1. Add new columns/tables in `src/core/database.py` `create_tables()` method
2. Update Pydantic models in `src/core/models.py`
3. Add migration logic if needed (currently no formal migrations)
4. Update both CLI and TUI layers to handle new fields

## Current Status & Known Issues (December 2024)

### Project State
- ✅ **CLI Mode**: Fully functional
- ❌ **TUI Mode**: Display and notes feature have issues
- ℹ️ **Development Phase**: Active development, database can be rebuilt as needed

### Known Issues

**CRITICAL: TUI Notes Save Failure**
- **Root Cause**: Database schema mismatch between CLI and TUI
  - CLI uses `src/project_manager_cli/services/database_service.py` (older schema without notes)
  - TUI uses `src/core/database.py` (enhanced schema with notes, favorites, etc.)
  - Different app data directories: `pyproject-cli` vs `project-manager-cli`
- **Impact**: Notes cannot be added/saved in TUI
- **Fix**: See implementation plan at `.claude/plans/hazy-floating-llama.md`

### Code Quality Issues Identified

**Comprehensive Review Completed**: December 2024
- **Full Report**: See agent review in conversation history
- **Implementation Plan**: `.claude/plans/hazy-floating-llama.md`

**Critical Issues:**
1. **Duplicate DatabaseManager classes** (HIGH) - Two different implementations causing schema drift
2. **Duplicate Config classes** (HIGH) - Inconsistent configuration between CLI/TUI
3. **Duplicate Models/Exceptions** (MEDIUM) - Duplicate Pydantic models in `core/` and `project_manager_cli/`
4. **Missing test suite** (CRITICAL) - No automated tests
5. **App directory mismatch** (CRITICAL) - CLI and TUI using different directories

**Architecture Issues:**
- Mixed import patterns (CLI importing from core, but also has own services)
- Missing type hints throughout codebase
- Inconsistent error handling patterns
- Embedded CSS/JS in Python files (560+ lines in `html_generator.py`)

**Planned Refactoring** (See plan file for details):
- Phase 1: Database schema consolidation & migration
- Phase 2: Remove duplicate core classes
- Phase 3: Fix architecture & import patterns
- Phase 4: Add comprehensive type hints
- Phase 5: Standardize error handling
- Phase 6: Create basic test suite

### OpenAI Configuration

**Valid Model**: `o4-mini` is the configured and tested OpenAI model
- Located in `src/project_manager_cli/config.py:81`
- This is NOT a typo - it's a valid, tested model
- Alternative model in `src/core/config.py:40` is `gpt-4o-mini`
- After consolidation, standardize on `o4-mini`

## Backward Compatibility

The project maintains compatibility with legacy implementations:
- `pyproject.py` script (original monolithic implementation) still present
- Existing `.pyprojectid` files recognized
- Database schema is backward compatible (adds columns, doesn't remove)
- Cursor `projects.json` format unchanged
