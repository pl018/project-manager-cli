"""Logging service for the project manager CLI."""

import json
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from termcolor import colored

from core.config_manager import config as Config


class _ConsoleFormatter(logging.Formatter):
    """Cleaner console formatter.

    - Keeps console output readable (no timestamps on every line).
    - Leaves timestamps in the file handler for audit/debugging.
    """

    def format(self, record: logging.LogRecord) -> str:
        message = record.getMessage()
        # Prefix non-INFO lines with level name for clarity.
        if record.levelno >= logging.WARNING:
            return f"{record.levelname}: {message}"
        return message


_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(text: str) -> str:
    return _ANSI_ESCAPE_RE.sub("", text or "")


class _FileFormatter(logging.Formatter):
    """File formatter that strips ANSI color codes so logs stay readable."""

    def format(self, record: logging.LogRecord) -> str:
        return _strip_ansi(super().format(record))


class LoggingManager:
    """Manages application logging."""
    
    def __init__(self):
        self.logger = None
        self.log_file_path = None
        
    def setup(self, test_mode: bool = False, project_uuid: Optional[str] = None) -> Tuple[logging.Logger, str]:
        """Configure logging."""
        
        logger = logging.getLogger('pyproject')
        logger.setLevel(logging.INFO)

        # Clear existing handlers for reconfiguration
        if logger.handlers:
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)

        file_formatter = _FileFormatter('%(asctime)s - %(levelname)s - %(message)s')
        console_formatter = _ConsoleFormatter()

        if test_mode:
            # Test mode: Only log to console, no file logging.
            self.log_file_path = "CONSOLE_ONLY" 
            console_handler = logging.StreamHandler(sys.stdout) # Explicitly use stdout
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        else:
            # Non-test mode: File logging (and console)
            file_handler_mode = 'w' # Default to overwrite for timestamped logs
            if project_uuid:
                log_file_name = f"{project_uuid}.log"
                log_dir = Path(Config._app_data_dir) / 'logs'
                os.makedirs(log_dir, exist_ok=True)
                self.log_file_path = str(log_dir / log_file_name)
                file_handler_mode = 'a' # Append for project-specific logs
            else:
                # Fallback if project_uuid is somehow None in non-test mode (should not happen with current logic)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                log_file_name = f"pyproject_log_{timestamp}.log"
                self.log_file_path = log_file_name # Store in CWD for general logs
            
            # File Handler
            file_handler = logging.FileHandler(self.log_file_path, mode=file_handler_mode, encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

            # Console Handler for non-test mode as well
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO) 
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)

        self.logger = logger
        return logger, self.log_file_path
        
    def write_receipt(self, project_data: Dict[str, Any], api_response: Optional[Dict[str, Any]] = None) -> None:
        """Write a human-readable receipt to the log (and console handler)."""
        if not self.logger:
            return

        # Show raw AI payload only when explicitly requested.
        # Keeps default UX clean, but preserves a way to debug prompts/responses.
        show_raw_ai = os.getenv("PMCLI_SHOW_RAW_AI_RESPONSE", "").strip().lower() in ("1", "true", "yes", "on")

        # Use a consistent border style
        border = "=" * 60
        section_break = "-" * 60

        # Color scheme (console); file handler will strip ANSI codes automatically.
        border_c = colored(border, "cyan")
        title_c = colored(f"{'PROJECT MANAGER RECEIPT':^60}", "cyan", attrs=["bold"])
        section_title = lambda s: colored(f"{s:^60}", "yellow", attrs=["bold"])
        label_c = lambda s: colored(f"{s:<25}", "cyan")
        dim_c = lambda s: colored(s, "white", attrs=["dark"])

        self.logger.info(f"\n{border_c}")
        self.logger.info(title_c)
        self.logger.info(f"{border_c}\n")
        
        # Project information
        self.logger.info(f"  {label_c('Project UUID:')} {project_data.get('uuid', 'N/A')}")
        self.logger.info(f"  {label_c('Project Name:')} {project_data.get('name', 'N/A')}")
        self.logger.info(f"  {label_c('Project Path:')} {project_data.get('root_path', 'N/A')}")
        description = project_data.get("description") or project_data.get("ai_app_description")
        if description:
            self.logger.info(f"  {label_c('Description:')} {description}")
        tags_value = project_data.get('tags', [])
        if isinstance(tags_value, str):
            try:
                import json as _json
                tags_value = _json.loads(tags_value)
            except Exception:
                # Fallback: split on commas if it's a plain string
                tags_value = [t.strip() for t in tags_value.split(',') if t.strip()]
        self.logger.info(f"  {label_c('Tags:')} {colored(', '.join(tags_value), 'green') if tags_value else dim_c('None')}")
        self.logger.info(
            f"  {label_c('Processed On:')} {project_data.get('last_updated', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}"
        )
        
        # AI-generated information if available
        ai_tags = project_data.get('ai_tags') # Assuming tags might be split between user and AI
        # If ai_info was part of project_data, extract from there.
        # For now, let's assume core AI info is directly in project_data
        ai_app_name = project_data.get('ai_app_name')
        ai_app_description = project_data.get('ai_app_description')

        if ai_tags or ai_app_name or ai_app_description:
            self.logger.info(f"\n{colored(section_break, 'cyan')}")
            self.logger.info(section_title("AI GENERATED INFORMATION"))
            self.logger.info(f"{colored(section_break, 'cyan')}\n")
            # Use project_data.get('tags') which should be the final list of tags for the project
            # The 'ai_tags_for_receipt' was a temporary thought, better to use the actual tags list
            actual_tags = project_data.get('tags', [])
            # Ensure ai_tags are not duplicated if they are already in the main tags list
            # For the receipt, we just want to show what the AI specifically suggested if available.
            # The main "Tags:" line in the receipt will show the combined list.
            # Let's use the ai_info_model.tags for specifically what AI suggested if that was passed in project_data
            # For now, project_data directly contains ai_app_name & ai_app_description.
            # The 'ai_tags' variable above is not correctly sourced. Let's assume ai_info_model content was flattened into project_data
            
            # For the AI specific part of the receipt, let's assume 'ai_tags_for_receipt' was populated in create_project_payload
            specific_ai_tags = project_data.get('ai_tags_for_receipt')
            if specific_ai_tags:
                 self.logger.info(f"  {label_c('AI Suggested Tags:')} {colored(', '.join(specific_ai_tags), 'green')}")
            if ai_app_name:
                self.logger.info(f"  {label_c('AI App Name:')} {ai_app_name}")
            if ai_app_description:
                self.logger.info(f"  {label_c('AI App Description:')} {ai_app_description}")
        
        # API response information if available
        if api_response:
            self.logger.info(f"\n{colored(section_break, 'cyan')}")
            self.logger.info(section_title("AI TAG GENERATION DETAILS"))
            self.logger.info(f"{colored(section_break, 'cyan')}\n")
            self.logger.info(f"  {label_c('Model:')} {api_response.get('model', 'N/A')}")
            self.logger.info(
                f"  {label_c('Token Usage:')} {api_response.get('usage', {}).get('total_tokens', 'N/A')} total tokens"
            )

            if show_raw_ai:
                # Format the raw response nicely (best-effort; never crash the receipt).
                raw_content_str = None
                try:
                    raw_content_str = api_response.get("choices", [{}])[0].get("message", {}).get("content")
                except Exception:
                    raw_content_str = None

                if raw_content_str:
                    try:
                        raw_content_json = json.loads(raw_content_str)
                        pretty_raw_content = json.dumps(raw_content_json, indent=2)
                        self.logger.info(f"\n  {label_c('Raw AI Response:')}\n{pretty_raw_content}")
                    except json.JSONDecodeError:
                        self.logger.info(f"\n  {label_c('Raw AI Response:')} {raw_content_str}")
                else:
                    self.logger.info(f"\n  {label_c('Raw AI Response:')} {dim_c('[unavailable]')}")
        
        self.logger.info(f"\n  {label_c('Log file location:')} {colored(os.path.abspath(self.log_file_path), 'cyan')}")
        self.logger.info(f"{border_c}\n")