"""Windows Explorer integration."""

import os
import subprocess

from .base import ToolIntegration


class ExplorerIntegration(ToolIntegration):
    """Integration with Windows Explorer."""

    def __init__(self):
        super().__init__(
            name="explorer",
            display_name="Explorer",
            icon="📁"
        )

    def is_available(self) -> bool:
        """Explorer is available on Windows."""
        return os.name == 'nt'

    def open_project(self, path: str) -> bool:
        """Open project folder in Windows Explorer by running 'ii .' in terminal."""
        try:
            if os.name == 'nt':  # Windows only
                # Open Windows Terminal (or cmd) and run 'ii .' (PowerShell Invoke-Item)
                if self.check_command("wt"):
                    subprocess.Popen(
                        ['wt', '-d', path, 'pwsh', '-c', 'ii .'],
                        creationflags=subprocess.DETACHED_PROCESS
                    )
                else:
                    subprocess.Popen(
                        ['cmd', '/c', f'cd /d {path} && pwsh -c ii .'],
                        creationflags=subprocess.DETACHED_PROCESS
                    )
                return True
            return False
        except Exception as e:
            print(f"Error opening Explorer: {e}")
            return False
