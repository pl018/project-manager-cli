"""Git repository utilities for project manager."""

import subprocess
from pathlib import Path
from typing import Tuple, Optional


class GitService:
    """Service for interacting with git repositories."""

    @staticmethod
    def is_git_repository(project_path: str) -> bool:
        """
        Check if directory is a git repository.

        Args:
            project_path: Path to check

        Returns:
            True if git repo, False otherwise
        """
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                cwd=project_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5,
                text=True
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False

    @staticmethod
    def has_uncommitted_changes(project_path: str) -> Tuple[bool, Optional[str]]:
        """
        Check if git repository has uncommitted changes.

        Args:
            project_path: Path to git repository

        Returns:
            Tuple of (has_changes: bool, status_output: str)
        """
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=project_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                text=True
            )

            if result.returncode != 0:
                return False, None

            status_output = result.stdout.strip()
            has_changes = len(status_output) > 0

            return has_changes, status_output

        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
            return False, f"Error: {str(e)}"
