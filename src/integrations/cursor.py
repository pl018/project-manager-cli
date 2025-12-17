"""Cursor IDE integration."""

import os
import subprocess
from pathlib import Path
from typing import Optional

from .base import ToolIntegration


class CursorIntegration(ToolIntegration):
    """Integration with Cursor IDE."""

    def __init__(self):
        super().__init__(
            name="cursor",
            display_name="Cursor",
            icon="⚡"
        )

    def is_available(self) -> bool:
        """Check if Cursor is installed."""
        # Check for cursor command
        if self.check_command("cursor"):
            return True

        # Check for Cursor in common installation paths
        if os.name == 'nt':  # Windows
            paths = [
                Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs' / 'cursor' / 'Cursor.exe',
                Path(os.environ.get('PROGRAMFILES', '')) / 'Cursor' / 'Cursor.exe',
            ]
        elif os.name == 'posix':  # macOS/Linux
            paths = [
                Path('/Applications/Cursor.app'),
                Path.home() / 'Applications' / 'Cursor.app',
                Path('/usr/local/bin/cursor'),
                Path.home() / '.local' / 'bin' / 'cursor',
            ]
        else:
            return False

        return any(path.exists() for path in paths)

    def open_project(self, path: str) -> bool:
        """Open a project in Cursor by launching terminal and running 'cursor .'"""
        try:
            if os.name == 'nt':  # Windows
                # Open Windows Terminal (or cmd) and run 'cursor .'
                if self.check_command("wt"):
                    subprocess.Popen(
                        ['wt', '-d', path, 'cmd', '/c', 'cursor .'],
                        creationflags=subprocess.DETACHED_PROCESS
                    )
                else:
                    subprocess.Popen(
                        ['cmd', '/c', f'cd /d {path} && cursor .'],
                        creationflags=subprocess.DETACHED_PROCESS
                    )
                return True

            elif os.name == 'posix':
                # macOS/Linux - open terminal and run 'cursor .'
                subprocess.Popen(
                    ['bash', '-c', f'cd "{path}" && cursor .'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                return True

            return False
        except Exception as e:
            print(f"Error opening Cursor: {e}")
            return False

    def open_file(self, file_path: str) -> bool:
        """Open a specific file in Cursor."""
        try:
            if not Path(file_path).exists():
                return False

            if os.name == 'nt':  # Windows
                subprocess.Popen(
                    ['cursor', file_path],
                    creationflags=subprocess.DETACHED_PROCESS,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                return True

            elif os.name == 'posix':
                # macOS/Linux
                subprocess.Popen(
                    ['cursor', file_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                return True

            return False
        except Exception as e:
            print(f"Error opening file in Cursor: {e}")
            return False

    def get_config_path(self) -> Optional[Path]:
        """Get Cursor's projects.json path."""
        if os.name == 'nt':  # Windows
            config_path = Path(os.environ.get('APPDATA', '')) / 'Cursor' / 'User' / 'globalStorage' / 'alefragnani.project-manager' / 'projects.json'
        elif os.name == 'posix':
            # macOS/Linux
            config_path = Path.home() / 'Library' / 'Application Support' / 'Cursor' / 'User' / 'globalStorage' / 'alefragnani.project-manager' / 'projects.json'
        else:
            return None

        return config_path if config_path.exists() else None
