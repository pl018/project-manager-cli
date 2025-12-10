# Installation Guide

## Prerequisites

- Python 3.8 or later
- [UV package manager](https://docs.astral.sh/uv/) (recommended) or pip

## Installation

### Using UV (Recommended)

1. **Install UV** (if not already installed):
   ```bash
   # On Windows (PowerShell)
   irm https://astral.sh/uv/install.ps1 | iex
   
   # On macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Install the Project Manager CLI**:
   ```bash
   # Install from local directory (development)
   uv pip install -e .
   
   # Or install from git repository
   uv pip install git+https://github.com/pl018/project-manager-cli.git
   ```

3. **Initialize the configuration**:
   ```bash
   project-manager-cli init
   ```

### Using pip

```bash
# Install from local directory
pip install -e .

# Initialize configuration
project-manager-cli init
```

## Initial Setup

After installation, run the initialization command:

```bash
project-manager-cli init
```

This will:
- Prompt you for the database location (with sensible defaults)
- Ask for your Cursor projects.json file location
- Optionally configure your OpenAI API key for AI tagging
- Create the configuration file at `~/.config/project-manager-cli/config.yaml`

### Configuration Options

During initialization, you'll be prompted for:

- **Database path**: Where to store the SQLite database
  - Default: `%APPDATA%\project-manager-cli\project_manager_data.db` (Windows)
  - Default: `~/.config/project-manager-cli/project_manager_data.db` (Linux/macOS)

- **Projects file**: Location of Cursor's projects.json file
  - Default: `%APPDATA%\Cursor\User\globalStorage\alefragnani.project-manager\projects.json`

- **OpenAI API Key**: Optional, for AI-powered project tagging

## Usage

### Basic Commands

```bash
# Run project analysis on current directory
project-manager-cli run

# Run on specific directory
project-manager-cli run /path/to/project

# Run in test mode (no changes saved)
project-manager-cli run --test

# Show current configuration
project-manager-cli config

# Reset configuration
project-manager-cli reset

# Show help
project-manager-cli --help
```

### Environment Variable Overrides

You can override configuration with environment variables:

```bash
# Override database path
export PROJECT_MANAGER_DB_PATH="/custom/path/to/database.db"

# Override projects file
export PROJECT_MANAGER_PROJECTS_FILE="/custom/path/to/projects.json"

# Set OpenAI API key
export OPENAI_API_KEY="your-api-key-here"
```

## Development Installation

For development:

```bash
# Clone the repository
git clone https://github.com/yourusername/project-manager-cli.git
cd project-manager-cli

# Create virtual environment and install in development mode
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/

# Lint
flake8 src/
```

## Troubleshooting

### Configuration Issues

If you encounter configuration issues:

1. Check your configuration:
   ```bash
   project-manager-cli config
   ```

2. Reset and reconfigure:
   ```bash
   project-manager-cli reset
   project-manager-cli init
   ```

3. Verify file permissions for the database and projects file directories

### Common Issues

- **Permission denied**: Ensure the database directory is writable
- **Cursor projects.json not found**: Verify the Cursor installation and projects file path
- **OpenAI API errors**: Check your API key is valid and has sufficient credits

For more help, see the [README.md](../../README.md) or open an issue on GitHub. 