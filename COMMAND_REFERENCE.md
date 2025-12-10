# Project Manager CLI - Command Reference

Quick reference guide for all CLI commands with examples.

## Table of Contents

- [Getting Started](#getting-started)
- [Initialization](#initialization)
- [Project Management](#project-management)
- [Listing & Filtering](#listing--filtering)
- [HTML Reports](#html-reports)
- [Configuration](#configuration)
- [Interactive UI](#interactive-ui)

---

## Getting Started

### Get Help

```bash
# Show main help
pm-cli --help

# Show help for specific command
pm-cli COMMAND --help
```

### Check Version

```bash
pm-cli --version
```

---

## Initialization

### `pm-cli init`

Initialize the CLI configuration.

```bash
# Interactive setup (recommended for first time)
pm-cli init

# Set all options at once
pm-cli init \
  --db-path ~/.myaibs/projects.db \
  --projects-file ~/AppData/Roaming/Cursor/User/globalStorage/projects.json \
  --openai-api-key sk-...

# Force reconfiguration
pm-cli init --force

# Set only database path (will prompt for others)
pm-cli init --db-path ~/my-projects.db
```

**Options:**
- `--db-path PATH` - Path to store the SQLite database
- `--projects-file PATH` - Path to Cursor projects.json file
- `--openai-api-key TEXT` - OpenAI API key for AI tagging
- `--force` - Overwrite existing configuration

---

## Project Management

### `pm-cli run`

Run the project manager on a directory to register/update it.

```bash
# Run on current directory
pm-cli run

# Run on specific directory
pm-cli run /path/to/my-project

# Test mode - analyze without saving changes
pm-cli run --test

# Test specific project
pm-cli run --test ~/projects/my-app
```

**Options:**
- `--test` - Run in test mode (no changes saved)

**Arguments:**
- `DIRECTORY` - Directory to analyze (defaults to current directory)

---

## Listing & Filtering

### `pm-cli list`

List all projects in a formatted table.

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

# Combine multiple filters
pm-cli list --favorites --tag python --search "api"
pm-cli list -f -t python -s api
```

**Options:**
- `-f, --favorites` - Show only favorite projects
- `-t, --tag TEXT` - Filter by tag (can be used multiple times)
- `-s, --search TEXT` - Search projects by name or path

---

## HTML Reports

### `pm-cli html`

Generate an interactive HTML page with project list.

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

**Options:**
- `--no-open` - Generate HTML but do not open in browser
- `-o, --output PATH` - Output file path (defaults to temp directory)

---

## Configuration

### `pm-cli config`

Show current configuration.

```bash
# View current configuration
pm-cli config
```

**No options**

---

### `pm-cli reset`

Reset configuration to defaults.

```bash
# Reset configuration (will prompt for confirmation)
pm-cli reset
```

**No options** (requires confirmation)

**Note:** This does NOT delete your project database, only the configuration file.

---

## Interactive UI

### `pm-cli tui`

Launch the interactive Terminal User Interface.

```bash
# Launch interactive UI
pm-cli tui
```

**Keyboard Navigation:**
- Arrow keys: Navigate through projects
- Enter: View project details
- `/`: Search projects
- `f`: Toggle favorites filter
- `q`: Quit
- `?`: Show help

**No options**

---

## Common Workflows

### First Time Setup

```bash
# 1. Initialize configuration
pm-cli init

# 2. Register your first project
cd /path/to/your/project
pm-cli run

# 3. View your projects
pm-cli list
```

### Adding Multiple Projects

```bash
# Register multiple projects
pm-cli run ~/projects/project1
pm-cli run ~/projects/project2
pm-cli run ~/projects/project3

# View all projects
pm-cli list
```

### Organizing Projects with Tags

```bash
# List projects by tag
pm-cli list --tag python
pm-cli list --tag web --tag frontend

# Search within tagged projects
pm-cli list --tag python --search "django"
```

### Creating Reports

```bash
# Generate HTML report
pm-cli html --output ~/reports/projects-$(date +%Y%m%d).html

# Generate report without opening
pm-cli html --no-open --output ~/weekly-report.html
```

### Testing Changes

```bash
# Test project registration without saving
pm-cli run --test ~/new-project

# Review in list (won't show up because test mode)
pm-cli list
```

---

## Tips & Tricks

### Short Options

Most commands have short options for faster typing:

```bash
pm-cli list -f -t python -s api    # Instead of --favorites --tag --search
pm-cli html -o report.html         # Instead of --output
```

### Combining Filters

You can combine multiple filters for precise results:

```bash
# Favorite Python projects with "api" in the name
pm-cli list -f -t python -s api

# Multiple tags (AND logic)
pm-cli list -t python -t web -t django
```

### Environment Variables

Override configuration with environment variables:

```bash
export PROJECT_MANAGER_DB_PATH="/custom/path/database.db"
export PROJECT_MANAGER_PROJECTS_FILE="/custom/projects.json"
export OPENAI_API_KEY="sk-..."
```

---

## Troubleshooting

### Configuration Not Found

```bash
❌ Configuration not found. Run 'pm-cli init' first.
```

**Solution:** Run `pm-cli init` to create configuration.

### Database Path Issues

If you need to change the database path:

```bash
# Reset and reconfigure
pm-cli reset
pm-cli init --db-path /new/path/database.db
```

### View Current Settings

```bash
# Check what's configured
pm-cli config
```

---

## Quick Reference Table

| Command | Short | Description | Example |
|---------|-------|-------------|---------|
| `init` | - | Initialize configuration | `pm-cli init` |
| `run` | - | Register/update project | `pm-cli run` |
| `list` | - | List all projects | `pm-cli list` |
| `--favorites` | `-f` | Filter favorites | `pm-cli list -f` |
| `--tag` | `-t` | Filter by tag | `pm-cli list -t python` |
| `--search` | `-s` | Search projects | `pm-cli list -s "my-app"` |
| `html` | - | Generate HTML report | `pm-cli html` |
| `--output` | `-o` | Output file path | `pm-cli html -o report.html` |
| `config` | - | Show configuration | `pm-cli config` |
| `reset` | - | Reset configuration | `pm-cli reset` |
| `tui` | - | Launch interactive UI | `pm-cli tui` |
| `--test` | - | Test mode (dry run) | `pm-cli run --test` |
| `--force` | - | Force operation | `pm-cli init --force` |
| `--no-open` | - | Don't open browser | `pm-cli html --no-open` |

---

## Additional Resources

- **Main Documentation**: See `README.md`
- **User Guides**: Check `.docs/user/` directory
- **Developer Docs**: Check `.docs/dev/` directory
- **CLI Help**: Run `pm-cli --help` or `pm-cli COMMAND --help`
- **TUI Help**: Press `?` in the TUI

---

**Made with ❤️ for developers who love the terminal**

