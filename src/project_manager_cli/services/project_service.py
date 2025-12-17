"""Project context service for the project manager CLI."""

import logging
import os
from pathlib import Path
from typing import Dict, Optional

from termcolor import colored

from core.config_manager import config as Config
from core.exceptions import ProjectManagerError
from core.models import ProjectInfo


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
            base_dir = Path.cwd()
            exclude_dirs = set(str(d) for d in (Config.EXCLUDE_DIRS or []))
            allowed_exts = set(str(e).lower() for e in (Config.IMPORTANT_EXTENSIONS or []))
            max_files = int(Config.MAX_FILES_TO_ANALYZE)

            self.logger.info(colored("Collecting file samples for AI tagging (README-first)...", "cyan"))

            # Prioritize README files so the AI understands the project "why/how" first.
            readme_candidates = [
                "README.md", "readme.md",
                "README.rst", "readme.rst",
                "README.txt", "readme.txt",
                "README", "readme",
            ]
            priority_files: list[str] = []
            for name in readme_candidates:
                p = base_dir / name
                if p.exists() and p.is_file():
                    priority_files.append(str(p))

            # Walk the tree and stop as soon as we have enough samples.
            selected_files: list[str] = []
            seen: set[str] = set()
            for f in priority_files:
                if f not in seen:
                    seen.add(f)
                    selected_files.append(f)

            if len(selected_files) < max_files:
                stop = False
                for root, dirnames, filenames in os.walk(base_dir, topdown=True):
                    # Prune excluded directories for performance
                    dirnames[:] = [d for d in dirnames if d not in exclude_dirs]

                    for filename in filenames:
                        p = Path(root) / filename
                        # Skip huge files early
                        try:
                            if p.stat().st_size > 1_000_000:
                                continue
                        except Exception:
                            continue

                        # Include README anywhere, otherwise filter by extension
                        name_lower = p.name.lower()
                        if name_lower.startswith("readme"):
                            pass
                        else:
                            ext = p.suffix.lower()
                            if ext not in allowed_exts:
                                continue

                        sp = str(p)
                        if sp in seen:
                            continue
                        seen.add(sp)
                        selected_files.append(sp)
                        if len(selected_files) >= max_files:
                            stop = True
                            break

                    if stop:
                        break
            
            if not selected_files:
                self.logger.warning(colored("No suitable files found for AI analysis", "yellow"))
                return None
                
            # Read content of selected files
            file_samples = {}
            total_chars = 0
            
            for file_path in selected_files:
                try:
                    # Already size-checked above, but keep a defensive guard
                    if os.path.getsize(file_path) > 1_000_000:
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

    def get_readme_summary(self, max_chars: int = 240) -> Optional[str]:
        """Best-effort short description derived from README (first meaningful line)."""
        try:
            readme_paths = [
                Path("README.md"), Path("readme.md"),
                Path("README.rst"), Path("readme.rst"),
                Path("README.txt"), Path("readme.txt"),
                Path("README"), Path("readme"),
            ]
            readme = next((p for p in readme_paths if p.exists() and p.is_file()), None)
            if not readme:
                return None

            text = readme.read_text(encoding="utf-8", errors="ignore")
            if not text:
                return None

            # Pick the first non-empty, non-badge-ish line.
            for raw_line in text.splitlines():
                line = raw_line.strip()
                if not line:
                    continue
                # Skip headings and common badge/image lines
                if line.startswith("#"):
                    continue
                if line.startswith("![") or line.startswith("[![") or "shields.io" in line.lower():
                    continue
                # Trim to a short sentence-ish snippet
                if len(line) > max_chars:
                    line = line[:max_chars].rstrip() + "…"
                return line
            return None
        except Exception:
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