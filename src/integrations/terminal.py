"""Terminal integration for opening projects in terminal emulators."""

import os
import platform
import subprocess
from pathlib import Path

from .base import ToolIntegration


class TerminalIntegration(ToolIntegration):
    """Integration with system terminal."""

    def __init__(self):
        super().__init__(
            name="terminal",
            display_name="Terminal",
            icon="⌨️"
        )

    def is_available(self) -> bool:
        """Terminal is always available."""
        return True

    def open_project(self, path: str) -> bool:
        """Open a terminal in the project directory."""
        try:
            system = platform.system()

            if system == "Windows":
                # Try Windows Terminal, fall back to cmd
                if self.check_command("wt"):
                    subprocess.Popen(
                        ['wt', '-d', path],
                        creationflags=subprocess.DETACHED_PROCESS
                    )
                else:
                    subprocess.Popen(
                        ['cmd', '/c', 'start', 'cmd', '/K', f'cd /d {path}'],
                        creationflags=subprocess.DETACHED_PROCESS
                    )
                return True

            elif system == "Darwin":  # macOS
                # Use osascript to open Terminal
                script = f'''
                tell application "Terminal"
                    do script "cd {path}"
                    activate
                end tell
                '''
                subprocess.Popen(
                    ['osascript', '-e', script],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                return True

            elif system == "Linux":
                # Try common terminal emulators
                terminals = [
                    'gnome-terminal',
                    'konsole',
                    'xfce4-terminal',
                    'xterm',
                    'alacritty',
                    'kitty',
                ]

                for term in terminals:
                    if self.check_command(term):
                        if term == 'gnome-terminal':
                            cmd = [term, '--working-directory', path]
                        elif term in ['konsole', 'xfce4-terminal']:
                            cmd = [term, '--workdir', path]
                        elif term in ['alacritty', 'kitty']:
                            cmd = [term, '--working-directory', path]
                        else:
                            cmd = [term, '-e', f'cd {path} && exec $SHELL']

                        subprocess.Popen(
                            cmd,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            start_new_session=True
                        )
                        return True

            return False
        except Exception as e:
            print(f"Error opening terminal: {e}")
            return False


class WarpIntegration(ToolIntegration):
    """Integration with Warp terminal."""

    def __init__(self):
        super().__init__(
            name="warp",
            display_name="Warp",
            icon="🚀"
        )

    def is_available(self) -> bool:
        """Check if Warp is installed."""
        if platform.system() == "Darwin":  # macOS only for now
            return Path('/Applications/Warp.app').exists()
        return self.check_command("warp")

    def open_project(self, path: str) -> bool:
        """Open project in Warp."""
        try:
            if platform.system() == "Darwin":
                subprocess.Popen(
                    ['open', '-a', 'Warp', path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                return True
            elif self.check_command("warp"):
                subprocess.Popen(
                    ['warp', path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                return True
            return False
        except Exception as e:
            print(f"Error opening Warp: {e}")
            return False
