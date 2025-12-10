"""Configuration module for the project manager CLI."""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import yaml


class ConfigManager:
    """Manages user configuration files."""
    
    def __init__(self):
        """Initialize the configuration manager."""
        self.config_dir = Path.home() / '.config' / 'project-manager-cli'
        self.config_file = self.config_dir / 'config.yaml'
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def config_exists(self) -> bool:
        """Check if configuration file exists."""
        return self.config_file.exists()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if not self.config_exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_file}")
        
        with open(self.config_file, 'r') as f:
            return yaml.safe_load(f) or {}
    
    def save_config(self, config_data: Dict[str, Any]) -> None:
        """Save configuration to file."""
        with open(self.config_file, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False, indent=2)
    
    def get_default_db_path(self) -> Path:
        """Get the default database path."""
        app_data_dir = Path(os.environ.get('APPDATA', Path.home() / '.config')) / 'project-manager-cli'
        return app_data_dir / 'project_manager_data.db'
    
    def get_default_projects_file(self) -> Path:
        """Get the default Cursor projects.json path."""
        return Path(os.environ.get('APPDATA', Path.home())) / 'Cursor' / 'User' / 'globalStorage' / 'alefragnani.project-manager' / 'projects.json'


class Config:
    """Application configuration that can be loaded from file or environment."""
    
    def __init__(self):
        """Initialize configuration."""
        self._config_manager = ConfigManager()
        self._config_data = self._load_configuration()
    
    def _load_configuration(self) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        if self._config_manager.config_exists():
            try:
                return self._config_manager.load_config()
            except Exception as e:
                logging.warning(f"Could not load config file: {e}. Using defaults.")
        
        # Return default configuration
        return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values."""
        config_manager = ConfigManager()
        return {
            'db_path': str(config_manager.get_default_db_path()),
            'projects_file': str(config_manager.get_default_projects_file()),
            'openai_api_key': os.environ.get("OPENAI_API_KEY"),
            'default_tag': "app",
            'max_files_to_analyze': 10,
            'max_content_length': 10000,
            'exclude_dirs': ['node_modules', 'venv', '.git', '__pycache__', 'dist', 'build', 'target', '.docs', '.vscode'],
            'important_extensions': ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs', '.c', '.cpp', 
                                   '.h', '.cs', '.php', '.rb', '.md', '.html', '.css', '.json', '.yml', '.yaml'],
            'openai_api_url': "https://api.openai.com/v1/chat/completions",
            'openai_model': "o4-mini",
            'openai_model_temperature': 1,
            'uuid_filename': ".pyprojectid",
        }
    
    @property
    def PROJECTS_FILE(self) -> str:
        """Get projects file path with environment variable override."""
        return os.environ.get('PROJECT_MANAGER_PROJECTS_FILE', self._config_data.get('projects_file'))
    
    @property
    def SQLITE_DB_PATH(self) -> str:
        """Get database path with environment variable override."""
        return os.environ.get('PROJECT_MANAGER_DB_PATH', self._config_data.get('db_path'))
    
    @property
    def DEFAULT_TAG(self) -> str:
        return self._config_data.get('default_tag', 'app')
    
    @property
    def MAX_FILES_TO_ANALYZE(self) -> int:
        return self._config_data.get('max_files_to_analyze', 10)
    
    @property
    def MAX_CONTENT_LENGTH(self) -> int:
        return self._config_data.get('max_content_length', 10000)
    
    @property
    def EXCLUDE_DIRS(self) -> list:
        return self._config_data.get('exclude_dirs', [])
    
    @property
    def IMPORTANT_EXTENSIONS(self) -> list:
        return self._config_data.get('important_extensions', [])
    
    @property
    def OPENAI_API_KEY(self) -> Optional[str]:
        return os.environ.get('OPENAI_API_KEY', self._config_data.get('openai_api_key'))
    
    @property
    def OPENAI_API_URL(self) -> str:
        return self._config_data.get('openai_api_url', "https://api.openai.com/v1/chat/completions")
    
    @property
    def OPENAI_MODEL(self) -> str:
        return self._config_data.get('openai_model', "o4-mini")
    
    @property
    def OPENAI_MODEL_TEMPERATURE(self) -> int:
        return self._config_data.get('openai_model_temperature', 1)
    
    @property
    def UUID_FILENAME(self) -> str:
        return self._config_data.get('uuid_filename', ".pyprojectid")
    
    @property
    def _app_data_dir(self) -> str:
        """Get the application data directory."""
        return str(Path(self.SQLITE_DB_PATH).parent)
    
    def validate(self) -> bool:
        """Validate required configuration."""
        from .exceptions import ConfigError
        
        # Validate projects file parent directory
        projects_file_parent_dir = Path(self.PROJECTS_FILE).parent
        if not projects_file_parent_dir.exists():
            try:
                os.makedirs(projects_file_parent_dir, exist_ok=True)
                logging.info(f"Created directory for PROJECTS_FILE: {projects_file_parent_dir}")
            except OSError as e:
                raise ConfigError(f"Parent directory for projects.json ({projects_file_parent_dir}) does not exist and could not be created: {e}")
        elif not os.access(projects_file_parent_dir, os.W_OK):
            raise ConfigError(f"Parent directory for projects.json ({projects_file_parent_dir}) is not writable.")
        
        # Validate SQLite DB directory
        sqlite_db_parent_dir = Path(self.SQLITE_DB_PATH).parent
        if not sqlite_db_parent_dir.exists():
            try:
                os.makedirs(sqlite_db_parent_dir, exist_ok=True)
                logging.info(f"Created directory for SQLite DB: {sqlite_db_parent_dir}")
            except OSError as e:
                raise ConfigError(f"SQLite DB directory ({sqlite_db_parent_dir}) does not exist and could not be created: {e}")
        elif not os.access(sqlite_db_parent_dir, os.W_OK):
            raise ConfigError(f"SQLite DB directory ({sqlite_db_parent_dir}) is not writable.")

        return True


# Global config instance
config = Config() 