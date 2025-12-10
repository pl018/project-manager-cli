# Usage Guide

## Commands

```bash
# Initialize configuration (prompts for paths)
pm-cli init

# Run on current directory
pm-cli run

# Run on a specific directory
pm-cli run /path/to/project

# Dry-run (no changes saved)
pm-cli run --test

# Show configuration
pm-cli config

# Reset configuration
pm-cli reset
```

## Options for `run`

- `--tag <name>`: Append a custom tag (normalized to one-word lowercase alphanumeric)
- `--folder`: Append the literal suffix "folder" to the project name
- `--skip-ai-tags`: Skip AI enrichment

Examples:

```bash
# Add a custom tag
pm-cli run --tag tools

# Skip AI tagging
pm-cli run --skip-ai-tags

# On a specific directory with both
pm-cli run --tag experiments --skip-ai-tags C:/path/to/project

## Tagging rules

- Tags are one-word, lowercase, and alphanumeric only.
- No colon subcategories or multi-word tags.
- The workspace/parent-folder tag is not added automatically.
- The project name indicates language via the dominant file extension (e.g., `MyApp.py`).
```

## Legacy entrypoints

For back-compat, you can still run the legacy script:

```bash
python pyproject.py --tag demo --skip-ai-tags
```

## Output artifacts

- `projects.json`: Regenerated from the DB into Cursor's storage path
- `logs/<uuid>.log`: Detailed per-project receipt in the app data logs folder
- `.pyprojectid`: Stable UUID at project root


