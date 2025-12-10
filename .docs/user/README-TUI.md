# Project Manager TUI 🚀

A beautiful, modern terminal-based project manager with multi-tool integration, AI-powered tagging, and rich note-taking capabilities.

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## ✨ Features

### 🎨 Beautiful TUI Interface
- Modern, colorful terminal interface built with Textual
- Intuitive keyboard navigation (vim-style)
- Mouse support for clicking
- Real-time search and filtering
- Responsive layout

### 🔌 Multi-Tool Integration
Open your projects in any of these tools with a single key press:
- **Cursor** - AI-first code editor
- **VS Code** / **VS Code Insiders** - Microsoft's popular editor
- **PyCharm** - Python IDE
- **WebStorm** - JavaScript/TypeScript IDE
- **IntelliJ IDEA** - Java IDE
- **Terminal** - System terminal
- **Warp** - Modern terminal (macOS)

### 🔍 Advanced Search & Filtering
- **Fuzzy search** across project names, paths, and notes
- **Tag filtering** with AND/OR modes
- **Favorites** filter for quick access
- **Sort options**: Name, Date, Frequency, Last Updated
- **Recent searches** history

### 🏷️ Smart Tagging System
- **AI-generated tags** using OpenAI
- **Color-coded tags** for visual organization
- **Custom tag icons**
- **Tag management** interface
- **Pre-defined tag library** for common project types

### 📝 Rich Notes
- **Markdown support** for formatted notes
- **Per-project notes** with preview
- **Inline editing** with syntax highlighting
- **Full-text search** in notes

### 📊 Project Statistics
- Track how many times you've opened each project
- Last opened timestamp
- Project metadata and AI descriptions
- Usage analytics

## 🚀 Quick Start

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd project-manager-cli
```

2. **Install dependencies**
```bash
pip install -r requirements-new.txt
```

3. **Set up OpenAI API (optional, for AI tagging)**
Create a `.env` file in the project root:
```env
OPENAI_API_KEY=your_api_key_here
```

4. **Run the TUI**
```bash
python main.py
```

### First Use

When you first run the TUI, you'll see an empty project list. To add projects:

1. Navigate to any project directory
2. Run the legacy CLI tool to register it:
   ```bash
   python pyproject.py
   ```
3. Return to the TUI and press `r` to refresh

Or import existing Cursor projects automatically!

## 🎮 Usage

### Keyboard Shortcuts

#### Global Navigation
- `j` or `↓` - Move down
- `k` or `↑` - Move up
- `Enter` - Open project detail
- `Esc` - Go back / Close
- `q` - Quit application
- `?` - Show help

#### Dashboard
- `/` - Focus search bar
- `n` - Add new project
- `r` - Refresh project list
- `f` - Toggle favorites filter

#### Project Detail
- `o` - Open in default tool
- `e` - Edit notes
- `f` - Toggle favorite
- `d` - Delete project
- `Esc` - Back to dashboard

### Mouse Support

Click on any element:
- **Project cards** - Open detail view
- **Buttons** - Execute actions
- **Tags** - Filter by tag
- **Search bar** - Focus input

## 📁 Project Structure

```
project-manager-cli/
├── src/
│   ├── core/              # Core functionality
│   │   ├── config.py      # Configuration
│   │   ├── database.py    # SQLite manager
│   │   ├── models.py      # Data models
│   │   └── exceptions.py  # Custom exceptions
│   ├── integrations/      # Tool integrations
│   │   ├── base.py        # Base integration interface
│   │   ├── cursor.py      # Cursor integration
│   │   ├── vscode.py      # VS Code integration
│   │   ├── terminal.py    # Terminal integration
│   │   ├── jetbrains.py   # JetBrains IDEs
│   │   └── registry.py    # Tool registry
│   └── ui/                # TUI components
│       ├── app.py         # Main application
│       ├── screens/       # Screen layouts
│       │   ├── dashboard.py
│       │   └── project_detail.py
│       └── widgets/       # Custom widgets
│           ├── project_card.py
│           ├── search_bar.py
│           └── tag_pill.py
├── main.py                # Entry point
├── pyproject.py           # Legacy CLI (backward compatible)
└── requirements-new.txt   # Dependencies
```

## 🗄️ Data Storage

All data is stored in a SQLite database at:
- **Windows**: `%APPDATA%\pyproject-cli\project_manager_data.db`
- **macOS/Linux**: `~/.config/pyproject-cli/project_manager_data.db`

### Database Schema

**Projects Table**
- UUID, name, path, tags
- AI-generated metadata
- Notes (markdown)
- Favorites, last opened, open count
- Color theme

**Tags Table**
- Name, color, icon
- Pre-populated with common tags

**Tool Configs Table**
- Per-project tool configurations
- Custom launch parameters

## 🎨 Customization

### Adding Custom Tags

Tags are automatically populated from the config, but you can add custom ones:

1. Edit `src/core/config.py`
2. Add to `DEFAULT_TAGS` dictionary:
```python
'my-tag': {'color': '#ff6b6b', 'icon': '🎯'}
```

### Adding New Tool Integrations

1. Create a new file in `src/integrations/`
2. Inherit from `ToolIntegration` base class
3. Implement `is_available()` and `open_project()` methods
4. Register in `src/integrations/registry.py`

Example:
```python
class MyEditorIntegration(ToolIntegration):
    def __init__(self):
        super().__init__(
            name="myeditor",
            display_name="My Editor",
            icon="✨"
        )

    def is_available(self) -> bool:
        return self.check_command("myeditor")

    def open_project(self, path: str) -> bool:
        subprocess.Popen(['myeditor', path])
        return True
```

### Theming

The TUI uses Textual's theming system. You can customize colors in `src/ui/app.py` by modifying the CSS.

## 🤝 Backward Compatibility

The new TUI is fully backward compatible with the original `pyproject.py` CLI tool:

- Existing `.pyprojectid` files are recognized
- Existing database is used
- Cursor integration still works
- All your existing projects are imported

## 🐛 Troubleshooting

### TUI doesn't start
- Ensure Python 3.8+ is installed
- Install Textual: `pip install textual`
- Check terminal compatibility: `python -m textual --version`

### Projects not showing
- Press `r` to refresh
- Check database location
- Verify projects have `.pyprojectid` files

### Tools not opening
- Ensure the tool is installed and in PATH
- Test manually: `cursor /path/to/project`
- Check tool integration in registry

### AI tagging not working
- Verify OpenAI API key in `.env`
- Check API quota and billing
- Test connection: `curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"`

## 📝 Development

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black src/
```

### Type Checking
```bash
mypy src/
```

## 🗺️ Roadmap

- [ ] Project templates
- [ ] Git integration (branch status, commit info)
- [ ] Project groups/workspaces
- [ ] Import from other project managers
- [ ] Export/backup functionality
- [ ] Custom keyboard shortcuts
- [ ] Theme customization UI
- [ ] Cloud sync (optional)

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Credits

Built with:
- [Textual](https://github.com/Textualize/textual) - TUI framework
- [Rich](https://github.com/Textualize/rich) - Terminal formatting
- [Pydantic](https://github.com/pydantic/pydantic) - Data validation
- [OpenAI](https://openai.com) - AI tagging

## 💬 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check the documentation
- Press `?` in the TUI for help

---

**Made with ❤️ for developers who love the terminal**
