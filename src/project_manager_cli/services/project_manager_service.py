"""Project manager service for the project manager CLI."""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List

from termcolor import colored

from core.config_manager import config as Config
from core.exceptions import ProjectManagerError
from core.models import ProjectInfo, AIGeneratedInfo, ProjectEntry
from .ai_service import AITaggingService
from .project_service import ProjectContext


class ProjectManager:
    """Manages project entries in Cursor Project Manager."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        
    def create_project_payload(self,
                               project_uuid: str,
                               project_info: ProjectInfo,
                               ai_service: AITaggingService,
                               project_context: ProjectContext,
                               custom_tag: Optional[str] = None,
                               skip_ai_tags: bool = False) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        """Create project data payload for SQLite DB."""
        api_response = None
        ai_info_model: Optional[AIGeneratedInfo] = None # Use AIGeneratedInfo model
        
        try:
            # Tag normalization helper: one-word, lowercase, alphanumeric only
            def normalize_tag(tag: str) -> str:
                if not tag:
                    return ""
                # Lowercase and remove all non-alphanumeric characters
                import re as _re
                cleaned = ''.join(ch for ch in tag.lower() if ch.isalnum())
                # Avoid empty strings and overly generic placeholders
                return cleaned

            tags: List[str] = []
            
            # Add custom tag if provided
            if custom_tag:
                norm = normalize_tag(custom_tag)
                if norm:
                    tags.append(norm)
            
            ai_generated_tags = []
            # Add AI-generated tags by default unless disabled
            if not skip_ai_tags:
                file_samples = project_context.get_file_samples()
                ai_info_model, api_response = ai_service.generate_tags(file_samples)
                if ai_info_model and ai_info_model.tags:
                    # Normalize AI tags and keep minimal unique set
                    for t in ai_info_model.tags:
                        nt = normalize_tag(t)
                        if nt:
                            ai_generated_tags.append(nt)
                    # Keep order while deduping
                    seen = set()
                    for t in ai_generated_tags:
                        if t not in seen:
                            seen.add(t)
                            tags.append(t)
            
            # Minimal set: cap to 3 tags, remove empties
            tags = [t for t in tags if t]
            tags = tags[:3]
            
            # For consistency: the identifying project name stored in the DB is always the project directory name.
            # AI can still generate a "friendly name" (ai_app_name) for display purposes, but we don't overwrite name.
            project_name = project_info.rootFolderName
                
            current_time_iso = datetime.now().isoformat()

            # Short description: prefer AI summary, otherwise fall back to README-derived summary.
            description = None
            if ai_info_model and ai_info_model.app_description:
                description = ai_info_model.app_description
            else:
                description = project_context.get_readme_summary()

            payload = {
                "uuid": project_uuid,
                "name": project_name,
                "root_path": project_info.rootFolderPath,
                "tags": tags, # Already normalized, minimal, and de-duplicated in-order
                "ai_app_name": ai_info_model.app_name if ai_info_model else None,
                "ai_app_description": ai_info_model.app_description if ai_info_model else None,
                "description": description,
                "date_added": current_time_iso, # Will be handled by DB logic for existing entries
                "last_updated": current_time_iso,
                "enabled": True,
                # Storing AI tags separately for clarity in receipt, if needed
                "ai_tags_for_receipt": ai_generated_tags 
            }
            
            self.logger.info(colored("✓ Project data payload created successfully", "green"))
            self.logger.info(colored(f"✓ Project name for DB: {payload['name']}", "green"))
            
            return payload, api_response
        except Exception as e:
            self.logger.error(colored(f"Error creating project data payload: {str(e)}", "red"))
            raise ProjectManagerError(f"Failed to create project data payload: {str(e)}")

    def regenerate_cursor_projects_json(self, db_manager) -> None: # Add type hint for db_manager later
        """Generate projects.json from SQLite data."""
        try:
            self.logger.info(colored("Regenerating projects.json for Cursor Project Manager...", "cyan"))
            # Core DatabaseManager exposes get_all_projects(enabled_only=True). Keep logic here resilient
            # in case db_manager is an older/newer implementation.
            if hasattr(db_manager, "get_all_projects"):
                projects_data = db_manager.get_all_projects(enabled_only=True)
            else:
                projects_data = db_manager.get_all_enabled_projects()
            
            cursor_project_entries = []
            for proj_dict in projects_data:
                # Map DB data to ProjectEntry Pydantic model
                # Tags may already be a list (core DatabaseManager parses JSON), or a JSON string in older DB layers.
                tags_value = proj_dict.get("tags") or []
                if isinstance(tags_value, str):
                    try:
                        db_tags = json.loads(tags_value)
                    except json.JSONDecodeError:
                        db_tags = []
                        self.logger.warning(
                            f"Could not parse tags JSON from DB for {proj_dict.get('uuid')}: {tags_value}"
                        )
                else:
                    db_tags = tags_value

                entry = ProjectEntry(
                    name=proj_dict['name'],
                    rootPath=proj_dict['root_path'],
                    paths=[],  # Default, as per original model
                    tags=db_tags, # This should be a list now
                    enabled=bool(proj_dict['enabled']),
                    project_uuid=proj_dict['uuid']
                )
                cursor_project_entries.append(entry.model_dump(exclude_none=True)) # Changed .dict() to .model_dump()

            # Write updated content
            with open(Config.PROJECTS_FILE, 'w', encoding='utf-8') as f:
                json.dump(cursor_project_entries, f, indent=4)

            self.logger.info(colored(f"✓ Successfully regenerated {Config.PROJECTS_FILE}", "green"))
            
            # Validate the updated file
            with open(Config.PROJECTS_FILE, 'r', encoding='utf-8') as f:
                json.load(f)
            self.logger.info(colored("✓ JSON validation successful for generated file", "green"))

        except Exception as e:
            self.logger.error(colored(f"Error regenerating {Config.PROJECTS_FILE}: {str(e)}", "red"))
            # Not raising ProjectManagerError here to avoid halting if only JSON generation fails
            # But it's a significant issue to log. 