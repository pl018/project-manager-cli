"""Cursor IDE integration."""

import json
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
        """Open a project in Cursor."""
        try:
            if self.check_command("cursor"):
                subprocess.Popen(
                    ['cursor', path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                return True

            # Try platform-specific approaches
            if os.name == 'nt':  # Windows
                cursor_path = self._find_windows_cursor()
                if cursor_path:
                    subprocess.Popen(
                        [str(cursor_path), path],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=subprocess.DETACHED_PROCESS
                    )
                    return True

            elif os.name == 'posix':
                # macOS
                if Path('/Applications/Cursor.app').exists():
                    subprocess.Popen(
                        ['open', '-a', 'Cursor', path],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True
                    )
                    return True

            return False
        except Exception as e:
            print(f"Error opening Cursor: {e}")
            return False

    def _find_windows_cursor(self) -> Optional[Path]:
        """Find Cursor executable on Windows."""
        paths = [
            Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs' / 'cursor' / 'Cursor.exe',
            Path(os.environ.get('PROGRAMFILES', '')) / 'Cursor' / 'Cursor.exe',
        ]
        for path in paths:
            if path.exists():
                return path
        return None

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
