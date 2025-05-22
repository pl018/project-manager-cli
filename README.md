# Cursor Project Updater

A utility script that automatically adds your current working directory to
Cursor Project Manager.

## Features

- Automatically registers current directory with Cursor Project Manager
- Adds intelligent default tags (parent folder name)
- Supports custom tags via command-line arguments
- Option to add "folder" suffix to project names
- Colored terminal output for better readability
- **AI Tagging**: Analyzes your repository files to automatically generate
  relevant project tags (enabled by default)
- Detailed logging with receipt of changes

## Requirements

- Python 3.6+
- termcolor package
- requests package (for AI tagging)
- python-dotenv package (for environment variable management)
- OpenAI API key (for AI tagging feature)

## Installation

1. Clone or download this repository
2. Install dependencies:

   ```powershell
   pip install termcolor requests python-dotenv
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

## Examples

Add current directory as a project (includes AI tagging by default):

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

1. Collects information about the current working directory
2. Creates a project entry with appropriate tags
3. By default, performs AI tagging:
   - Analyzes up to 10 files from your repository
   - Uses OpenAI to determine project purpose
   - Generates 2-3 descriptive tags automatically
4. Updates the Cursor Project Manager's configuration file
5. Validates the updated configuration
6. Creates a detailed log file as a receipt of the operation

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
