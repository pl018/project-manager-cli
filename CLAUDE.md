# CLAUDE.md

This file provides essential guidance to Claude Code when working with this repository.

## Project Overview

Project Manager CLI is a Python-based cross-platform project management tool with **two interfaces**:
- **CLI Mode** (`pm-cli`): Command-line interface for managing projects
- **GUI Mode** (`pm-gui`): Desktop GUI built with PySide6 (Qt)

Both share a SQLite database backend with Cursor IDE integration, AI-powered tagging via OpenAI, and multi-tool support.

**Note**: TUI mode has been removed. The `src/ui/` directory should be deleted if still present.

## Quick Reference

### Setup
```bash
pip install -e .              # Install in dev mode
pm-cli init                   # Initialize configuration
```

### Key Commands
```bash
pm-cli run [path]             # Register project
pm-cli list                   # List projects
pm-gui                        # Launch GUI
```

## Architecture Essentials

### Directory Structure
```
src/
├── core/                     # Shared foundation (database, models, config)
├── integrations/             # IDE/tool integrations (Cursor, VS Code, JetBrains)
├── project_manager_cli/      # CLI application
└── project_manager_desktop/  # GUI application
```

### Entry Points
- CLI: `src/project_manager_cli/cli.py:main()`
- GUI: `src/project_manager_desktop/main.py:main()`

### Database
- SQLite with auto-migration in `src/core/database.py`
- Tables: `projects`, `tags`, `tool_configs`, `search_history`
- UUID-based project identity (`.pyprojectid` files)

### Configuration
- User config: `%APPDATA%/project-manager-cli/config.yaml` (Windows) or `~/.config/project-manager-cli/config.yaml` (Unix)
- Environment variables: `PROJECT_MANAGER_DB_PATH`, `OPENAI_API_KEY`

## Critical Information

### Known Issues & Bugs

**See detailed analysis**: `~/.claude/plans/zazzy-discovering-sloth.md`

**Critical bugs to fix**:
1. 🔴 **Missing imports** in `src/project_manager_cli/services/project_service.py:179,184`
   - Add: `import glob` and `import re`
   - Method: `detect_dominant_extension()` will fail without these

2. 🟠 **VSCodeIntegration exists but not registered** in `src/integrations/registry.py`
   - Either add to registry or remove dead code

3. 🟠 **No transaction management** for archive operations
   - Archive creation not atomic (ZIP + delete + DB update can leave inconsistent state)

4. 🟡 **Inconsistent error handling** - services return `None` instead of raising exceptions

### OpenAI Configuration
- Valid model: `o4-mini` (in `src/project_manager_cli/config.py`)
- Alternative: `gpt-4o-mini` (in `src/core/config.py`)
- After bug fixes, standardize on one model name

## Development Notes

### Adding Tool Integrations
- Extend `ToolIntegration` ABC from `src/integrations/base.py`
- Implement: `is_available()`, `open_project()`, optionally `open_file()`, `get_config_path()`
- Register in `src/integrations/registry.py`

### Database Schema Changes
- Add columns in `database.py:create_tables()`
- Update Pydantic models in `core/models.py`
- Auto-migration handles backward compatibility

## Cross-Platform Notes
- Use `pathlib.Path` consistently
- Safe emoji handling in CLI (`safe_emoji()` function)
- Platform-specific paths handled in `Config.get_default_db_path()`

## Recent Changes

### December 2024
- ✅ Archive & hard delete features completed
- ✅ GUI enhancements (Edit tab, Docs tab, Delete functionality)
- ✅ Refactoring completed (consolidated database, config, models)
- ⚠️ TUI mode removed - focus on CLI and GUI only

### Cleanup Required
- [ ] Delete `src/ui/` directory (TUI code)
- [ ] Remove `main.py` (TUI entry point) if exists
- [ ] Update dependencies to remove `textual`
- [ ] Fix critical bugs listed above

## Documentation & Plans

### Project Plans (in this repo)
- Project-specific plans: `.claude/plans/` (local to this repository)
  - `gui-enhancements.md` - GUI feature implementation (completed)
  - `tui-enhancements.md` - TUI features (obsolete - TUI removed)

### User Plans (global)
- **Current bug analysis**: `~/.claude/plans/zazzy-discovering-sloth.md` (detailed code analysis)
- **Quick primer**: `~/.claude/plans/QUICK-PRIMER.md` (task overview)

### Other Documentation
- **README**: Project overview and installation instructions
- **pyproject.toml**: Dependencies and package configuration

---

**Note**: Use `~/.claude/plans/` for user-level plans, `.claude/plans/` for project-level plans
