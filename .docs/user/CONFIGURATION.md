# Configuration

The CLI uses a YAML configuration file plus environment variables for overrides.

## Locations

- Windows: `%APPDATA%/project-manager-cli/config.yaml`
- Linux/macOS: `~/.config/project-manager-cli/config.yaml`

## Keys

- `db_path`: Path to the SQLite database file
- `projects_file`: Cursor Project Manager `projects.json` path
- `openai_api_key`: Optional API key for AI tagging
- `max_files_to_analyze`: Max files sampled for AI (default: 10)
- `max_content_length`: Max chars per file sample (default: 10000)
- `exclude_dirs`: Directories to ignore for AI sampling
- `important_extensions`: File extensions used for AI sampling and language suffix
- `openai_model`, `openai_model_temperature`, `openai_api_url`: AI settings

## Environment overrides

Set these to override config values:

```bash
export PROJECT_MANAGER_DB_PATH="/custom/path/to/project_manager_data.db"
export PROJECT_MANAGER_PROJECTS_FILE="/custom/path/to/projects.json"
export OPENAI_API_KEY="sk-..."
```

On Windows (PowerShell):

```powershell
$env:PROJECT_MANAGER_DB_PATH = "C:\\path\\to\\project_manager_data.db"
$env:PROJECT_MANAGER_PROJECTS_FILE = "C:\\path\\to\\projects.json"
$env:OPENAI_API_KEY = "sk-..."
```

## Validating configuration

The app validates that parent directories for the DB and projects file exist and are writable, creating them if needed. If validation fails, you’ll see a descriptive error.


