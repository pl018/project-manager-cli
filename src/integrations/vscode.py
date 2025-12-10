"""Visual Studio Code integration."""

import os
import subprocess
from pathlib import Path
from typing import Optional

from .base import ToolIntegration


class VSCodeIntegration(ToolIntegration):
    """Integration with Visual Studio Code."""

    def __init__(self, insiders: bool = False):
        self.insiders = insiders
        command = "code-insiders" if insiders else "code"
        display_name = "VS Code Insiders" if insiders else "VS Code"

        super().__init__(
            name=command,
            display_name=display_name,
            icon="📘"
        )

    def is_available(self) -> bool:
        """Check if VS Code is installed."""
        return self.check_command(self.name)

    def open_project(self, path: str) -> bool:
        """Open a project in VS Code."""
        try:
            subprocess.Popen(
                [self.name, path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            return True
        except Exception as e:
            print(f"Error opening VS Code: {e}")
            return False

    def get_config_path(self) -> Optional[Path]:
        """Get VS Code's settings path."""
        if os.name == 'nt':  # Windows
            base = Path(os.environ.get('APPDATA', ''))
            folder = 'Code - Insiders' if self.insiders else 'Code'
        elif os.name == 'posix':
            if Path('/Applications').exists():  # macOS
                base = Path.home() / 'Library' / 'Application Support'
            else:  # Linux
                base = Path.home() / '.config'
            folder = 'Code - Insiders' if self.insiders else 'Code'
        else:
            return None

        config_path = base / folder / 'User' / 'settings.json'
        return config_path if config_path.exists() else None
