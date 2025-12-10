#!/usr/bin/env python3
"""
Backward compatibility entry point for the project manager CLI.
This file maintains the original entry point but uses the refactored modules.
"""

# Import the main function from the new package structure
from src.project_manager_cli.main import main

if __name__ == "__main__":
    main() 