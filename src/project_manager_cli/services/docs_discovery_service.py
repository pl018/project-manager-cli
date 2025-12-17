"""Documentation file discovery service for markdown file browsing."""

import os
from datetime import datetime
from pathlib import Path
from typing import List

from core.models import DocFile


class DocsDiscoveryService:
    """Service for discovering markdown documentation files in projects."""

    # Directories to exclude from search
    EXCLUDED_DIRS = {
        'node_modules', 'venv', '.venv', 'env', '.git', '__pycache__',
        'dist', 'build', '.next', '.nuxt', 'target', 'out', '.pytest_cache',
        '.tox', 'htmlcov', 'site-packages', '.vscode', '.idea', '.eggs',
        'vendor', 'bower_components', 'coverage'
    }

    # File extensions to search for
    DOC_EXTENSIONS = {'.md', '.markdown'}

    # Maximum number of files to return
    MAX_FILES = 500

    @staticmethod
    def discover_docs(project_path: str) -> List[DocFile]:
        """
        Discover markdown documentation files in a project.

        Args:
            project_path: Root path of the project

        Returns:
            List of DocFile objects sorted with README first, then alphabetically
        """
        project_root = Path(project_path)
        if not project_root.exists():
            return []

        doc_files = []
        readme_files = []

        try:
            # Walk through directory tree
            for root, dirs, files in os.walk(project_root):
                # Filter out excluded directories
                dirs[:] = [d for d in dirs if d not in DocsDiscoveryService.EXCLUDED_DIRS]

                # Process files
                for filename in files:
                    file_path = Path(root) / filename
                    extension = file_path.suffix.lower()

                    # Check if it's a markdown file
                    if extension in DocsDiscoveryService.DOC_EXTENSIONS:
                        try:
                            stat = file_path.stat()
                            relative_path = str(file_path.relative_to(project_root))

                            doc_file = DocFile(
                                filename=filename,
                                full_path=file_path,
                                relative_path=relative_path,
                                extension=extension,
                                size_bytes=stat.st_size,
                                modified_date=datetime.fromtimestamp(stat.st_mtime)
                            )

                            # Separate README files for priority sorting
                            if filename.lower().startswith('readme'):
                                readme_files.append(doc_file)
                            else:
                                doc_files.append(doc_file)

                            # Stop if we've reached the maximum
                            if len(readme_files) + len(doc_files) >= DocsDiscoveryService.MAX_FILES:
                                break

                        except (OSError, PermissionError):
                            # Skip files we can't access
                            continue

                # Stop walking if we've reached the maximum
                if len(readme_files) + len(doc_files) >= DocsDiscoveryService.MAX_FILES:
                    break

        except (OSError, PermissionError):
            # Handle permission errors at the directory level
            pass

        # Sort README files first, then other files alphabetically
        readme_files.sort(key=lambda x: x.filename.lower())
        doc_files.sort(key=lambda x: x.filename.lower())

        # Combine with README files first
        result = readme_files + doc_files

        return result[:DocsDiscoveryService.MAX_FILES]

    @staticmethod
    def search_docs(docs: List[DocFile], query: str) -> List[DocFile]:
        """
        Filter documentation files by search query.

        Args:
            docs: List of DocFile objects
            query: Search query string

        Returns:
            Filtered list of DocFile objects
        """
        if not query:
            return docs

        query_lower = query.lower()
        filtered = []

        for doc in docs:
            # Search in filename and relative path
            if (query_lower in doc.filename.lower() or
                query_lower in doc.relative_path.lower()):
                filtered.append(doc)

        return filtered
