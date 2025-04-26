# Cursor Project Updater

A utility script that automatically adds your current working directory to
Cursor Project Manager.

## Features

- Automatically registers current directory with Cursor Project Manager
- Adds intelligent default tags (parent folder name and "app" tag)
- Supports custom tags via command-line arguments
- Option to add "folder" suffix to project names
- Colored terminal output for better readability

## Requirements

- Python 3.6+
- termcolor package

## Installation

1. Clone or download this repository
2. Install dependencies:
   ```
   pip install termcolor
   ```

## Usage

Run the script from the directory you want to add to Cursor Project Manager:

```bash
python pyproject.py [options]
```

### Options

- `--folder`: Add "folder" suffix to the root folder name
- `--tag TAG`: Add a custom tag to the project

## Examples

Add current directory as a project:

```bash
python pyproject.py
```

Add current directory with "folder" suffix:

```bash
python pyproject.py --folder
```

Add current directory with custom tag:

```bash
python pyproject.py --tag frontend
```

## How It Works

The script:

1. Collects information about the current working directory
2. Creates a project entry with appropriate tags
3. Updates the Cursor Project Manager's configuration file
4. Validates the updated configuration

## File Structure

The code is organized in a modular fashion, separating concerns between:

- Parameter validation
- Project context resolution
- File path management
- Core business logic

## Error Handling

The script provides comprehensive error handling with user-friendly messages
for:

- Invalid JSON in projects file
- Missing projects file
- Permission issues
- General exceptions
