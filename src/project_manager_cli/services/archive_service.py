"""Archive service for backing up projects."""

import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Callable

from core.config import Config


class ArchiveService:
    """Service for archiving projects to ZIP files."""

    # Folders to delete before archiving
    LIBRARY_FOLDERS = [
        'node_modules',
        'venv', '.venv', 'env', '.env',
        '__pycache__',
        'dist', 'build',
        'target',
        '.next', '.nuxt',
        'vendor',
        'bower_components',
    ]

    @staticmethod
    def get_archive_directory() -> Path:
        """Get or create the archives directory."""
        archive_dir = Config._app_data_dir / 'archives'
        archive_dir.mkdir(parents=True, exist_ok=True)
        return archive_dir

    @staticmethod
    def generate_archive_filename(project_uuid: str, project_dir_name: str) -> str:
        """
        Generate archive filename.

        Format: {uuid}_{project-dir-name}_YYYY-MM-DD.zip
        """
        date_str = datetime.now().strftime('%Y-%m-%d')
        # Sanitize project dir name for filename
        safe_name = "".join(c for c in project_dir_name if c.isalnum() or c in ('-', '_'))
        return f"{project_uuid}_{safe_name}_{date_str}.zip"

    @staticmethod
    def find_library_folders(project_path: str) -> List[Path]:
        """
        Find library folders to delete in project.

        Args:
            project_path: Root path of project

        Returns:
            List of Path objects for folders to delete
        """
        project_root = Path(project_path)
        folders_to_delete = []

        for root, dirs, files in os.walk(project_root):
            # Check if any directory matches library folders
            for dir_name in dirs:
                if dir_name in ArchiveService.LIBRARY_FOLDERS:
                    folder_path = Path(root) / dir_name
                    folders_to_delete.append(folder_path)

            # Don't recurse into library folders
            dirs[:] = [d for d in dirs if d not in ArchiveService.LIBRARY_FOLDERS]

        return folders_to_delete

    @staticmethod
    def delete_library_folders(
        project_path: str,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> List[str]:
        """
        Delete library folders from project.

        Args:
            project_path: Root path of project
            progress_callback: Optional callback for progress updates

        Returns:
            List of deleted folder paths (for logging)
        """
        folders = ArchiveService.find_library_folders(project_path)
        deleted = []

        for folder in folders:
            try:
                if progress_callback:
                    progress_callback(f"Deleting {folder.name}...")

                # Use shutil.rmtree to recursively delete
                shutil.rmtree(folder, ignore_errors=True)
                deleted.append(str(folder))

            except Exception as e:
                # Log but continue (non-critical)
                if progress_callback:
                    progress_callback(f"Warning: Could not delete {folder.name}: {e}")

        return deleted

    @staticmethod
    def create_zip_archive(
        project_path: str,
        archive_path: Path,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        Create ZIP archive of project.

        Args:
            project_path: Root path of project
            archive_path: Destination ZIP file path
            progress_callback: Optional callback for progress updates

        Returns:
            True if successful, False otherwise
        """
        project_root = Path(project_path)

        try:
            if progress_callback:
                progress_callback(f"Creating archive {archive_path.name}...")

            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Walk through all files
                for root, dirs, files in os.walk(project_root):
                    # Skip .git directory
                    if '.git' in dirs:
                        dirs.remove('.git')

                    for file in files:
                        file_path = Path(root) / file
                        # Calculate relative path for archive
                        arcname = file_path.relative_to(project_root)

                        try:
                            zipf.write(file_path, arcname)
                        except (OSError, PermissionError):
                            # Skip files we can't read
                            if progress_callback:
                                progress_callback(f"Warning: Skipped {arcname}")

            if progress_callback:
                size_mb = archive_path.stat().st_size / (1024 * 1024)
                progress_callback(f"Archive created: {size_mb:.2f} MB")

            return True

        except Exception as e:
            if progress_callback:
                progress_callback(f"Error creating archive: {e}")
            return False

    @staticmethod
    def get_archive_size_mb(archive_path: Path) -> float:
        """Get archive size in megabytes."""
        try:
            return archive_path.stat().st_size / (1024 * 1024)
        except OSError:
            return 0.0
