"""Base interface for tool integrations."""

import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class ToolIntegration(ABC):
    """Base class for tool integrations."""

    def __init__(self, name: str, display_name: str, icon: str = "🔧"):
        self.name = name
        self.display_name = display_name
        self.icon = icon

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this tool is installed and available."""
        pass

    @abstractmethod
    def open_project(self, path: str) -> bool:
        """Open a project in this tool."""
        pass

    def get_config_path(self) -> Optional[Path]:
        """Get the tool's configuration file path if applicable."""
        return None

    def check_command(self, command: str) -> bool:
        """Check if a command is available in PATH."""
        return shutil.which(command) is not None

    def __str__(self):
        return f"{self.icon} {self.display_name}"

    def __repr__(self):
        return f"ToolIntegration(name={self.name}, available={self.is_available()})"
