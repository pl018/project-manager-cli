# Quick Start Guide 🚀

Get up and running with Project Manager TUI in 5 minutes!

## Step 1: Install Dependencies

```bash
pip install -r requirements-new.txt
```

## Step 2: (Optional) Set Up AI Tagging

Create a `.env` file in the project root:

```bash
echo "OPENAI_API_KEY=your_api_key_here" > .env
```

Or skip AI tagging by running with `--skip-ai-tags`

## Step 3: Launch the TUI

```bash
python main.py
```

You should see a beautiful terminal interface!

## Step 4: Add Your First Project

### Method 1: From the TUI (Coming Soon)
Press `n` to add a new project

### Method 2: Using the Legacy CLI
Navigate to your project directory and run:

```bash
cd /path/to/your/project
python pyproject.py
```

Then return to the TUI and press `r` to refresh!

## Navigation Basics

### Keyboard Shortcuts
- `↑` `↓` or `j` `k` - Navigate up/down
- `/` - Search
- `Enter` - Open project details
- `o` - Open in default editor
- `f` - Toggle favorites
- `q` - Quit

### Mouse
- Click on project cards to view details
- Click on tags to filter
- Click buttons to execute actions

## What's Next?

### Explore Features
1. **Search** - Press `/` and type to search
2. **Tags** - Click tags to filter projects
3. **Notes** - Open a project and press `e` to add notes
4. **Tools** - Open projects in Cursor, VS Code, PyCharm, etc.

### Customize
1. Edit `src/core/config.py` to add custom tags
2. Modify `src/ui/app.py` CSS for custom themes
3. Add new tool integrations in `src/integrations/`

## Common Tasks

### Import Existing Cursor Projects
Your existing Cursor projects should be automatically available!
If not, they're stored at:
- Windows: `%APPDATA%\Cursor\User\globalStorage\alefragnani.project-manager\projects.json`
- macOS: `~/Library/Application Support/Cursor/...`

### Backup Your Data
Database location:
- Windows: `%APPDATA%\pyproject-cli\project_manager_data.db`
- macOS/Linux: `~/.config/pyproject-cli/project_manager_data.db`

Just copy this file to back up all your projects, notes, and tags!

### Add a Project with Custom Tags
```bash
cd /path/to/project
python pyproject.py --tag frontend --tag react
```

## Tips & Tricks

1. **Favorites** - Star your most-used projects for quick access
2. **Notes** - Use markdown for rich formatting
3. **Multiple Tools** - Configure different tools per project
4. **Search** - Search includes project names, paths, AND notes
5. **Statistics** - Check project detail to see usage stats

## Need Help?

- Press `?` in the TUI for keyboard shortcuts
- Check `README-TUI.md` for full documentation
- Open an issue on GitHub

**Happy coding! 🎉**
