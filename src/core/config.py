"""Application configuration."""

import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration constants and environment variables."""

    # Version
    VERSION = "2.0.0"
    APP_NAME = "Project Manager TUI"

    # Cursor Integration (backward compatibility)
    PROJECTS_FILE = os.path.join(
        os.environ.get('APPDATA', str(Path.home() / '.config')),
        'Cursor', 'User', 'globalStorage',
        'alefragnani.project-manager', 'projects.json'
    )

    # Database Configuration
    UUID_FILENAME = ".pyprojectid"
    SQLITE_DB_NAME = "project_manager_data.db"

    # App data directory
    _app_data_dir = Path(os.environ.get('APPDATA', str(Path.home() / '.config'))) / 'pyproject-cli'
    os.makedirs(_app_data_dir, exist_ok=True)
    SQLITE_DB_PATH = str(_app_data_dir / SQLITE_DB_NAME)
    LOG_DIR = _app_data_dir / 'logs'
    os.makedirs(LOG_DIR, exist_ok=True)

    # AI Configuration
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
    OPENAI_MODEL = "gpt-4o-mini"
    OPENAI_MODEL_TEMPERATURE = 1

    # File Analysis Settings
    MAX_FILES_TO_ANALYZE = 10
    MAX_CONTENT_LENGTH = 10000
    EXCLUDE_DIRS = [
        'node_modules', 'venv', '.git', '__pycache__',
        'dist', 'build', 'target', '.docs', '.vscode',
        '.idea', 'vendor', 'cache', '.next'
    ]
    IMPORTANT_EXTENSIONS = [
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go',
        '.rs', '.c', '.cpp', '.h', '.cs', '.php', '.rb',
        '.md', '.html', '.css', '.json', '.yml', '.yaml',
        '.toml', '.ini', '.conf', '.vue', '.svelte'
    ]

    # UI Theme Configuration
    THEME = {
        'primary': '#3b82f6',      # Blue
        'success': '#10b981',      # Green
        'warning': '#f59e0b',      # Yellow
        'error': '#ef4444',        # Red
        'accent': '#8b5cf6',       # Purple
        'muted': '#6b7280',        # Gray
    }

    # Tool Integration Settings
    SUPPORTED_TOOLS = [
        'cursor',
        'vscode',
        'code-insiders',
        'pycharm',
        'webstorm',
        'intellij',
        'terminal',
        'warp',
        'iterm2'
    ]

    # Default Tags
    DEFAULT_TAGS = {
        'python': {'color': '#3776ab', 'icon': '🐍'},
        'javascript': {'color': '#f7df1e', 'icon': '⚡'},
        'typescript': {'color': '#3178c6', 'icon': '📘'},
        'web': {'color': '#e34c26', 'icon': '🌐'},
        'api': {'color': '#009688', 'icon': '🔌'},
        'frontend': {'color': '#61dafb', 'icon': '🎨'},
        'backend': {'color': '#43853d', 'icon': '⚙️'},
        'mobile': {'color': '#3ddc84', 'icon': '📱'},
        'cli': {'color': '#4d4d4d', 'icon': '⌨️'},
        'library': {'color': '#563d7c', 'icon': '📚'},
    }

    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration."""
        # Ensure projects file parent directory exists for Cursor integration
        projects_file_parent_dir = Path(cls.PROJECTS_FILE).parent
        if not projects_file_parent_dir.exists():
            try:
                os.makedirs(projects_file_parent_dir, exist_ok=True)
            except OSError:
                # Not critical if Cursor isn't installed
                pass

        # Validate SQLite DB directory
        sqlite_db_parent_dir = Path(cls.SQLITE_DB_PATH).parent
        if not sqlite_db_parent_dir.exists():
            raise Exception(f"SQLite DB directory does not exist: {sqlite_db_parent_dir}")

        if not os.access(sqlite_db_parent_dir, os.W_OK):
            raise Exception(f"SQLite DB directory is not writable: {sqlite_db_parent_dir}")

        return True
