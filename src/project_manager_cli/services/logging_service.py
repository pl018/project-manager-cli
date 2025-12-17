"""Logging service for the project manager CLI."""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from core.config_manager import config as Config


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

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        if test_mode:
            # Test mode: Only log to console, no file logging.
            self.log_file_path = "CONSOLE_ONLY" 
            console_handler = logging.StreamHandler(sys.stdout) # Explicitly use stdout
            console_handler.setLevel(logging.INFO)
            test_formatter = logging.Formatter('%(asctime)s - TEST - %(levelname)s - %(message)s')
            console_handler.setFormatter(test_formatter)
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
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

            # Console Handler for non-test mode as well
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO) 
            console_handler.setFormatter(formatter) 
            logger.addHandler(console_handler)

        self.logger = logger
        return logger, self.log_file_path
        
    def write_receipt(self, project_data: Dict[str, Any], api_response: Optional[Dict[str, Any]] = None) -> None:
        """Write a detailed receipt to the log file."""
        if not self.logger:
            return

        # Use a consistent border style
        border = "=" * 60
        section_break = "-" * 60

        self.logger.info(f"\n{border}")
        self.logger.info(f"{'PROJECT MANAGER RECEIPT':^60}")
        self.logger.info(f"{border}\n")
        
        # Project information
        self.logger.info(f"  {'Project UUID:':<25} {project_data.get('uuid', 'N/A')}")
        self.logger.info(f"  {'Project Name:':<25} {project_data.get('name', 'N/A')}")
        self.logger.info(f"  {'Project Path:':<25} {project_data.get('root_path', 'N/A')}")
        tags_value = project_data.get('tags', [])
        if isinstance(tags_value, str):
            try:
                import json as _json
                tags_value = _json.loads(tags_value)
            except Exception:
                # Fallback: split on commas if it's a plain string
                tags_value = [t.strip() for t in tags_value.split(',') if t.strip()]
        self.logger.info(f"  {'Tags:':<25} {', '.join(tags_value)}")
        self.logger.info(f"  {'Processed On:':<25} {project_data.get('last_updated', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}")
        
        # AI-generated information if available
        ai_tags = project_data.get('ai_tags') # Assuming tags might be split between user and AI
        # If ai_info was part of project_data, extract from there.
        # For now, let's assume core AI info is directly in project_data
        ai_app_name = project_data.get('ai_app_name')
        ai_app_description = project_data.get('ai_app_description')

        if ai_tags or ai_app_name or ai_app_description:
            self.logger.info(f"\n{section_break}")
            self.logger.info(f"{'AI GENERATED INFORMATION':^60}")
            self.logger.info(f"{section_break}\n")
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
                 self.logger.info(f"  {'AI Suggested Tags:':<25} {', '.join(specific_ai_tags)}")
            if ai_app_name:
                name_status = "(Used as project name)" if project_data.get('name') == ai_app_name else ""
                self.logger.info(f"  {'AI App Name:':<25} {ai_app_name} {name_status}")
            if ai_app_description:
                self.logger.info(f"  {'AI App Description:':<25} {ai_app_description}")
        
        # API response information if available
        if api_response:
            self.logger.info(f"\n{section_break}")
            self.logger.info(f"{'AI TAG GENERATION DETAILS':^60}")
            self.logger.info(f"{section_break}\n")
            self.logger.info(f"  {'Model:':<25} {api_response.get('model', 'N/A')}")
            
            # Format the raw response nicely
            raw_content_str = api_response['choices'][0]['message']['content']
            try:
                # Attempt to parse and pretty-print if it's JSON
                raw_content_json = json.loads(raw_content_str)
                pretty_raw_content = json.dumps(raw_content_json, indent=2)
                self.logger.info(f"  {'Raw Response:':<25}\n{pretty_raw_content}")
            except json.JSONDecodeError:
                # If not JSON, print as is
                self.logger.info(f"  {'Raw Response:':<25} {raw_content_str}")
            
            self.logger.info(f"  {'Token Usage:':<25} {api_response.get('usage', {}).get('total_tokens', 'N/A')} total tokens")
        
        self.logger.info(f"\n  {'Log file location:':<25} {os.path.abspath(self.log_file_path)}")
        self.logger.info(f"{border}\n") 