# Cursor Project Updater

A utility script that automatically adds your current working directory to
Cursor Project Manager, now with enhanced data management using UUIDs and an SQLite database.

## Features

- Automatically registers current directory with Cursor Project Manager
- **UUID-based Project Identification**: Each project is assigned a unique UUID, stored in a `.pyprojectid` file at the project root, ensuring persistent identity.
- **SQLite Database Backend**: Project metadata is stored in a robust SQLite database (`project_manager_data.db` located in user's app data directory), preventing duplicates and enabling efficient data management.
- **Automated `projects.json` Generation**: The `projects.json` file for Cursor Project Manager is automatically generated from the SQLite database.
- Adds intelligent default tags (parent folder name)
- Supports custom tags via command-line arguments
- Option to add "folder" suffix to project names
- Colored terminal output for better readability
- **AI Tagging**: Analyzes your repository files to automatically generate
  relevant project tags, app name, and description (enabled by default).
- **Per-Project Logging**: Detailed logging receipts are stored in UUID-named files (e.g., `<uuid>.log`) in the user's app data directory, providing a history of operations for each project.
- **Test Mode**: `--test` flag allows running the script without making changes to the database, `.pyprojectid`, or `projects.json`, with logs directed to the console.

## Requirements

- Python 3.7+ (due to `pathlib` usage and f-strings)
- `pydantic` (for data validation)
- `termcolor` package
- `requests` package (for AI tagging)
- `python-dotenv` package (for environment variable management)
- OpenAI API key (for AI tagging feature)

## Installation

1. Clone or download this repository
2. Install dependencies:

   ```powershell
   pip install pydantic termcolor requests python-dotenv
   ```

3. Compile the Code into a .exe file:

   ```powershell
   pyinstaller --onefile pyproject.py
   ```

4. For AI tagging feature, set your OpenAI API key:
   - Create a `.env` file in the same directory as the script
   - Add `OPENAI_API_KEY=your_api_key_here` to the file
   - Or set it as an environment variable
5. Install the script as a global command:

   ```powershell
   python -m pip install --upgrade pyproject.py
   ```

### PowerShell Integration

To make the script globally available in PowerShell, add the following to your
PowerShell profile:

1. Open PowerShell and check if a profile exists:

   ```powershell
   Test-Path $PROFILE
   ```

2. If it returns False, create a new profile:

   ```powershell
   New-Item -Path $PROFILE -Type File -Force
   ```

3. Open the profile in a text editor:

   ```powershell
   notepad $PROFILE
   ```

4. Add the following function (update the script path to match your
   installation):

   ```powershell
   function pyproject {
       param([Parameter(ValueFromRemainingArguments=$true)]$params)
       
       # Get the full path to the script
       $scriptPath = "C:\path\to\your\pyproject.py"
       
       # Call the Python script with all parameters passed to this function
       if ($params) {
           python $scriptPath $params
       } else {
           python $scriptPath
       }
   }
   ```

5. Save and close the file

6. Reload your profile:

   ```powershell
   . $PROFILE
   ```

Now you can use the `pyproject` command directly in PowerShell.

## Usage

Run the script from the directory you want to add to Cursor Project Manager:

```bash
python pyproject.py [options]
```

Or if using PowerShell with the profile setup:

```powershell
pyproject [options]
```

### Options

- `--folder`: Add "folder" suffix to the root folder name
- `--tag TAG`: Add a custom tag to the project
- `--skip-ai-tags`: Disable AI tag generation (AI tagging is enabled by default)
- `--test`: Run in test mode. No changes are made to the database, `.pyprojectid` file, or `projects.json`. Logging is directed to the console.

## Examples

Add current directory as a project (includes AI tagging by default):

```bash
python pyproject.py
```

Run in test mode:

```bash
python pyproject.py --test
```

Add current directory with "folder" suffix:

```bash
python pyproject.py --folder
```

Add current directory with custom tag:

```bash
python pyproject.py --tag frontend
```

Add current directory without AI-generated tags:

```bash
python pyproject.py --skip-ai-tags
```

Combine options:

```bash
python pyproject.py --folder --tag frontend
```

## How It Works

The script:

1. **Identifies Project**: Checks for a `.pyprojectid` file in the current directory. If not found (and not in test mode), generates a new UUID and saves it to `.pyprojectid`.
2. **Initializes Database**: Connects to an SQLite database (`project_manager_data.db` in user's app data). Creates tables if they don't exist.
3. **Collects Information**: Gathers details about the current working directory.
4. **AI Analysis (Optional)**: By default, performs AI tagging:
   - Analyzes repository files.
   - Uses OpenAI to determine project purpose, suggest a name, description, and descriptive tags.
5. **Updates Database**: Adds or updates the project's metadata in the SQLite database using the project's UUID as the key.
6. **Generates Cursor PM File**: Regenerates the `projects.json` file from the data in the SQLite database, ensuring Cursor Project Manager has the latest information.
7. **Logs Operation**: Writes a detailed receipt to a UUID-named log file in the user's app data directory (e.g., `logs/<uuid>.log`). In test mode, logs to console.

## Data Management

- **`.pyprojectid`**: A file created at the root of your project containing a unique UUID. This file should ideally be committed to your project's version control to maintain a consistent identity across different environments.
- **`project_manager_data.db`**: An SQLite database stored in `%APPDATA%\pyproject-cli` (Windows) or `~/.config/pyproject-cli` (Linux/macOS). This is the central source of truth for all projects managed by this script.
- **Log Files**: Individual log files, named by project UUID (e.g., `uuid.log`), are stored in a `logs` subdirectory within the same application data directory as the database. These provide a history of processing for each project.
- **`projects.json`**: The file used by the Cursor Project Manager extension. This script now generates this file based on the contents of the SQLite database.

## File Structure

The code is organized in a modular fashion, separating concerns between:

- Parameter validation
- Project context resolution
- File path management
- Core business logic
- AI file analysis and tag generation
- Logging and receipt generation

## Error Handling

The script provides comprehensive error handling with user-friendly messages
for:

- Invalid JSON in projects file
- Missing projects file
- Permission issues
- API connection errors
- General exceptions

```plaintext
project-manager-cli
├─ .cursor
│  └─ rules
│     ├─ code-structure.mdc
│     ├─ powershell-integration.mdc
│     └─ project-overview.mdc
├─ pyproject.py
├─ README.md
└─ requirements.txt

```
