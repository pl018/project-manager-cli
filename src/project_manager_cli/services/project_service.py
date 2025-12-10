"""Project context service for the project manager CLI."""

import glob
import logging
import os
import re
from pathlib import Path
from typing import Dict, Optional

from termcolor import colored

from ..config import config as Config
from ..exceptions import ProjectManagerError
from ..models import ProjectInfo


class ProjectContext:
    """Handles project context detection and information collection."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        
    def get_project_info(self, is_folder: bool = False) -> ProjectInfo:
        """Get project information from current working directory."""
        try:
            cwd = Path.cwd()
            cwd_name = cwd.name
            
            project_info = ProjectInfo(
                rootFolderName=f"{cwd_name}folder" if is_folder else cwd_name,
                rootFolderPath=str(cwd),
                ParentRootFolderName=cwd.parent.name,
                cwdfolderName=cwd_name
            )
            self.logger.info(colored(f"✓ Project information collected successfully", "green"))
            return project_info
        except Exception as e:
            self.logger.error(colored(f"Error collecting project information: {str(e)}", "red"))
            raise ProjectManagerError(f"Failed to collect project information: {str(e)}")

    def get_file_samples(self) -> Optional[Dict[str, str]]:
        """Collects file samples from the repository for AI analysis."""
        try:
            # Create exclude pattern from directories to exclude
            exclude_pattern = re.compile(f'({"|".join(Config.EXCLUDE_DIRS)})')
            
            # Get all files recursively
            all_files = []
            for ext in Config.IMPORTANT_EXTENSIONS:
                pattern = f"**/*{ext}"
                files = [f for f in glob.glob(pattern, recursive=True) 
                         if not exclude_pattern.search(f)]
                all_files.extend(files)
            
            # Limit to the most important files
            selected_files = all_files[:Config.MAX_FILES_TO_ANALYZE]
            
            if not selected_files:
                self.logger.warning(colored("No suitable files found for AI analysis", "yellow"))
                return None
                
            # Read content of selected files
            file_samples = {}
            total_chars = 0
            
            for file_path in selected_files:
                try:
                    if os.path.getsize(file_path) > 1000000:  # Skip files > 1MB
                        continue
                        
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(Config.MAX_CONTENT_LENGTH)
                        file_samples[file_path] = content
                        total_chars += len(content)
                        
                        # If we've collected enough content, stop
                        if total_chars >= Config.MAX_CONTENT_LENGTH * 3:
                            break
                except Exception as e:
                    self.logger.warning(colored(f"Warning: Could not read {file_path}: {str(e)}", "yellow"))
                    
            self.logger.info(colored(f"✓ Analyzed {len(file_samples)} files for AI tagging", "green"))
            return file_samples
        except Exception as e:
            self.logger.warning(colored(f"Error collecting file samples: {str(e)}", "yellow"))
            return None 

    def detect_dominant_extension(self) -> Optional[str]:
        """Detect the dominant file extension in the project.

        Picks the most frequent extension from IMPORTANT_EXTENSIONS, ignoring excluded directories.
        Returns the extension string (e.g., ".py") or None if nothing is found.
        """
        try:
            exclude_pattern = re.compile(f'({"|".join(Config.EXCLUDE_DIRS)})')
            extension_to_count: Dict[str, int] = {}

            for ext in Config.IMPORTANT_EXTENSIONS:
                pattern = f"**/*{ext}"
                files = [f for f in glob.glob(pattern, recursive=True) if not exclude_pattern.search(f)]
                if files:
                    extension_to_count[ext] = extension_to_count.get(ext, 0) + len(files)

            if not extension_to_count:
                return None

            # Choose the extension with the highest count; tie-breaker by alphabetical order for determinism
            dominant_ext = sorted(extension_to_count.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
            return dominant_ext
        except Exception:
            return None