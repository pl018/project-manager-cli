"""JetBrains IDEs integration."""

import os
import subprocess
from pathlib import Path
from typing import Optional

from .base import ToolIntegration


class JetBrainsIntegration(ToolIntegration):
    """Base class for JetBrains IDE integrations."""

    def __init__(self, name: str, display_name: str, icon: str, commands: list):
        super().__init__(name, display_name, icon)
        self.commands = commands  # List of possible command names

    def is_available(self) -> bool:
        """Check if this JetBrains IDE is installed."""
        return any(self.check_command(cmd) for cmd in self.commands)

    def open_project(self, path: str) -> bool:
        """Open a project in this JetBrains IDE."""
        try:
            for cmd in self.commands:
                if self.check_command(cmd):
                    subprocess.Popen(
                        [cmd, path],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True
                    )
                    return True
            return False
        except Exception as e:
            print(f"Error opening {self.display_name}: {e}")
            return False


class PyCharmIntegration(JetBrainsIntegration):
    """Integration with PyCharm."""

    def __init__(self):
        super().__init__(
            name="pycharm",
            display_name="PyCharm",
            icon="🐍",
            commands=["pycharm", "charm", "pycharm-professional", "pycharm-community"]
        )


class WebStormIntegration(JetBrainsIntegration):
    """Integration with WebStorm."""

    def __init__(self):
        super().__init__(
            name="webstorm",
            display_name="WebStorm",
            icon="🌐",
            commands=["webstorm", "wstorm"]
        )


class IntelliJIntegration(JetBrainsIntegration):
    """Integration with IntelliJ IDEA."""

    def __init__(self):
        super().__init__(
            name="intellij",
            display_name="IntelliJ IDEA",
            icon="💡",
            commands=["idea", "intellij-idea-community", "intellij-idea-ultimate"]
        )
