"""
Project Manager CLI - A tool for managing project metadata and Cursor integration.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .cli import main
from .app import Application
from core.config_manager import DynamicConfig as Config, ConfigManager

__all__ = ["main", "Application", "Config", "ConfigManager"] 