"""
Project Manager CLI - A tool for managing project metadata and Cursor integration.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

def main() -> None:
    """
    Lazy entry point kept for backward compatibility.

    NOTE: Do not import `project_manager_cli.cli` at module import time.
    Importing it here can cause `python -m project_manager_cli.cli ...` to emit:
      RuntimeWarning: 'project_manager_cli.cli' found in sys.modules ...
    """
    from .cli import main as _main

    _main()

__all__ = ["main"]