#!/usr/bin/env python3
"""
Project Manager TUI - Entry Point

A beautiful terminal-based project manager with multi-tool integration.
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.ui.app import run_tui
from src.core.config import Config


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Project Manager TUI - A beautiful terminal project manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    Launch the TUI interface
  %(prog)s --version          Show version information
  %(prog)s --help             Show this help message

For more information, visit: https://github.com/yourusername/project-manager-cli
        """
    )

    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {Config.VERSION}'
    )

    parser.add_argument(
        '--cli',
        action='store_true',
        help='Use CLI mode (legacy pyproject.py compatibility)'
    )

    args = parser.parse_args()

    if args.cli:
        # Legacy CLI mode - use the old pyproject.py functionality
        print("Legacy CLI mode not yet implemented.")
        print("Please use the TUI by running: python main.py")
        sys.exit(1)
    else:
        # Launch TUI
        try:
            run_tui()
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            sys.exit(0)
        except Exception as e:
            print(f"\nError: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
