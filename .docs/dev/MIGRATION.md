# Migration Guide: v1.x → v2.0 (TUI)

## Overview

Version 2.0 introduces a beautiful TUI interface while maintaining full backward compatibility with the original CLI tool.

## What's Changed?

### New Features ✨
- Beautiful terminal UI built with Textual
- Multi-tool integration (not just Cursor)
- Advanced search and filtering
- Rich notes with markdown support
- Color-coded tags
- Project statistics and usage tracking

### Backward Compatible ✅
- All existing `.pyprojectid` files work
- Existing database is used (with schema enhancements)
- Original `pyproject.py` CLI still works
- Cursor integration unchanged

## Migration Steps

### 1. Install New Dependencies

```bash
pip install -r requirements-new.txt
```

Key new dependencies:
- `textual` - TUI framework
- `rich` - Terminal formatting
- `pydantic>=2.0` - Updated data validation

### 2. Database Migration

The database will be **automatically upgraded** when you first run the new version!

New tables added:
- `tags` - Tag definitions with colors and icons
- `tool_configs` - Per-project tool configurations
- `search_history` - Search history

New columns in `projects`:
- `notes` - Rich text notes
- `favorite` - Favorite flag
- `last_opened` - Last opened timestamp
- `open_count` - Usage counter
- `color_theme` - Color theme preference

**Your existing data is preserved!**

### 3. Launch the TUI

```bash
python main.py
```

All your existing projects will be there!

## Using Both Versions

You can use both the TUI and CLI:

### TUI (Recommended)
```bash
python main.py
```

### Legacy CLI
```bash
python pyproject.py [options]
```

They share the same database, so changes are synchronized!

## Feature Comparison

| Feature | v1.x (CLI) | v2.0 (TUI) |
|---------|------------|------------|
| Project registration | ✅ | ✅ (coming soon) |
| AI tagging | ✅ | ✅ |
| Cursor integration | ✅ | ✅ |
| VS Code integration | ❌ | ✅ |
| Other editors | ❌ | ✅ |
| Visual interface | ❌ | ✅ |
| Search & filter | ❌ | ✅ |
| Notes | ❌ | ✅ |
| Favorites | ❌ | ✅ |
| Statistics | ❌ | ✅ |
| Tag management | ❌ | ✅ |

## Common Questions

### Will my existing projects work?
**Yes!** All existing projects are automatically imported.

### Do I need to re-register my projects?
**No!** They're already in the database.

### Can I still use the CLI?
**Yes!** `pyproject.py` still works exactly as before.

### What about my Cursor projects.json?
**Still works!** The TUI generates it from the database just like v1.x.

### Will AI tagging still work?
**Yes!** Same OpenAI integration, now with better UI.

### Can I go back to v1.x?
**Yes!** The database changes are backward compatible. Just keep both versions.

## New Workflows

### Adding Projects

**Before (v1.x):**
```bash
cd /path/to/project
python pyproject.py --tag frontend
```

**Now (v2.0):**
```bash
# Option 1: Use TUI (coming soon)
python main.py
# Press 'n' to add new project

# Option 2: Still use CLI
cd /path/to/project
python pyproject.py --tag frontend

# Then in TUI, press 'r' to refresh
```

### Finding Projects

**Before (v1.x):**
- Open Cursor
- Use Project Manager extension

**Now (v2.0):**
```bash
python main.py
# Press '/' to search
# Type project name
# Press Enter to open
```

### Opening Projects

**Before (v1.x):**
- Only Cursor

**Now (v2.0):**
- Cursor, VS Code, PyCharm, WebStorm, IntelliJ, Terminal, Warp
- One-key launch from TUI
- Or click the tool button

## Troubleshooting

### "Module not found" errors
Install new dependencies:
```bash
pip install -r requirements-new.txt
```

### Projects not showing in TUI
Press `r` to refresh, or check:
```bash
ls ~/.config/pyproject-cli/  # macOS/Linux
dir %APPDATA%\pyproject-cli\  # Windows
```

### Database errors
Backup and rebuild:
```bash
# Backup
cp ~/.config/pyproject-cli/project_manager_data.db backup.db

# Rebuild (will preserve data)
python main.py
```

### Tool integrations not working
Ensure tools are in PATH:
```bash
which cursor  # macOS/Linux
where cursor  # Windows
```

## Rollback (If Needed)

If you need to go back to v1.x:

1. **Keep your database** - It's compatible!
2. **Use the old requirements.txt:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Continue using:**
   ```bash
   python pyproject.py
   ```

The database schema is backward compatible, so v1.x will work (just won't show new fields).

## Getting Help

- Check [README-TUI.md](../user/README-TUI.md) for full documentation
- Run `python main.py` and press `?` for help
- Open an issue on GitHub

## Feedback Welcome!

This is a major upgrade. We'd love to hear:
- What you like
- What could be better
- Feature requests
- Bug reports

**Enjoy the new TUI! 🚀**
