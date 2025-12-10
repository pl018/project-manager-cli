# Project Manager CLI (Cursor Project Updater)

A cross-platform CLI that registers your current directory with the Cursor Project Manager extension. It persists project metadata in SQLite, assigns a stable UUID per project, and regenerates Cursor's `projects.json` from the database. Optional AI tagging can infer tags, an app name, and a description from your codebase.

## Features

- **Single command registration**: Add the current directory as a project in Cursor
- **Stable project identity**: `.pyprojectid` stores a UUID at project root
- **SQLite backend**: Prevents duplicates and enables reliable updates
- **Auto-generate `projects.json`**: Built from the DB for Cursor integration
- **Tagging**: One-word lowercase alphanumeric tags; add your own with `--tag`.
- **Language in name**: Project name is suffixed with dominant file extension (e.g., `MyApp.py`).
- **Optional AI enrichment**: Generate tags, app name, and description
- **Per-project receipts**: Detailed logs for each processed project
- **Test mode**: Dry-run without writing DB, files, or IDs

## Quickstart

1) Install (dev mode shown; see Install guide for alternatives):

```bash
pip install -e .
```

2) Initialize configuration (prompts for DB path and Cursor `projects.json`):

```bash
pm-cli init
```

3) Register the current directory:

```bash
pm-cli run
```

More commands and examples are in [USAGE.md](USAGE.md).

## Configuration

- Configuration file: `~/.config/project-manager-cli/config.yaml` (Windows uses `%APPDATA%\project-manager-cli\config.yaml`)
- Environment overrides: `PROJECT_MANAGER_DB_PATH`, `PROJECT_MANAGER_PROJECTS_FILE`, `OPENAI_API_KEY`

Details in [CONFIGURATION.md](CONFIGURATION.md).

## AI Tagging (optional)

Set `OPENAI_API_KEY` to enable AI enrichment. The CLI samples files and asks the model for minimal, one-word alphanumeric tags (no subcategories). Tags are normalized and capped to 2–3. Disable with `--skip-ai-tags`.

## Data locations

- **SQLite DB**: `%APPDATA%/project-manager-cli/project_manager_data.db` (Windows) or `~/.config/project-manager-cli/project_manager_data.db`
- **Cursor projects.json**: `%APPDATA%/Cursor/User/globalStorage/alefragnani.project-manager/projects.json`
- **Logs**: `%APPDATA%/project-manager-cli/logs/<uuid>.log`
- **Project UUID file**: `<project>/.pyprojectid`

## Development

- Install and dev commands are in [INSTALL.md](INSTALL.md)
- Project layout is documented in [STRUCTURE.md](STRUCTURE.md)

## Legacy usage

For backward compatibility you can still run the legacy entry point:

```bash
python pyproject.py [options]
```

## Troubleshooting

Common issues and fixes are in [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
