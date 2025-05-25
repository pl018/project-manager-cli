#!/usr/bin/env python3

import json
import os
import sys
import argparse
import glob
import re
import logging
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from termcolor import colored
import requests
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError

# Load environment variables from .env file
load_dotenv()

# -------------------- Configuration --------------------

class Config:
    """Application configuration constants and environment variables."""
    PROJECTS_FILE = os.path.join(os.environ['APPDATA'], 'Cursor', 'User', 'globalStorage', 
                                'alefragnani.project-manager', 'projects.json')
    DEFAULT_TAG = "app"  # Reference constant
    MAX_FILES_TO_ANALYZE = 10
    MAX_CONTENT_LENGTH = 10000  # Characters per file to analyze
    EXCLUDE_DIRS = ['node_modules', 'venv', '.git', '__pycache__', 'dist', 'build', 'target', '.docs', '.vscode']
    IMPORTANT_EXTENSIONS = ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs', '.c', '.cpp', 
                           '.h', '.cs', '.php', '.rb', '.md', '.html', '.css', '.json', '.yml', '.yaml']
                           
    # API Configuration
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
    OPENAI_MODEL = "o4-mini"
    OPENAI_MODEL_TEMPERATURE = 1
    
    # New UUID and SQLite Configuration
    UUID_FILENAME = ".pyprojectid"
    SQLITE_DB_NAME = "project_manager_data.db"
    
    # Determine a good user-specific app data directory for the SQLite DB
    # This will place it alongside the Cursor project manager file if possible, or in a dedicated folder.
    _app_data_dir = Path(os.environ.get('APPDATA', Path.home() / '.config')) / 'pyproject-cli'
    os.makedirs(_app_data_dir, exist_ok=True)
    SQLITE_DB_PATH = str(_app_data_dir / SQLITE_DB_NAME)
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration."""
        # PROJECTS_FILE is now generated, so we check its parent directory.
        projects_file_parent_dir = Path(cls.PROJECTS_FILE).parent
        if not projects_file_parent_dir.exists():
            # Attempt to create it if it's within the known Project Manager structure
            try:
                os.makedirs(projects_file_parent_dir, exist_ok=True)
                logging.info(f"Created directory for PROJECTS_FILE: {projects_file_parent_dir}")
            except OSError as e:
                raise ConfigError(f"Parent directory for projects.json ({projects_file_parent_dir}) does not exist and could not be created: {e}")
        elif not os.access(projects_file_parent_dir, os.W_OK):
            raise ConfigError(f"Parent directory for projects.json ({projects_file_parent_dir}) is not writable.")
        
        # Validate that the SQLite DB directory is writable
        sqlite_db_parent_dir = Path(cls.SQLITE_DB_PATH).parent
        if not sqlite_db_parent_dir.exists(): # Should have been created by os.makedirs in Config
             raise ConfigError(f"SQLite DB directory ({sqlite_db_parent_dir}) does not exist. This indicates an issue with initial path setup.")
        if not os.access(sqlite_db_parent_dir, os.W_OK):
            raise ConfigError(f"SQLite DB directory ({sqlite_db_parent_dir}) is not writable.")

        return True

# -------------------- Data Models --------------------

class ProjectInfo(BaseModel):
    """Project information model."""
    rootFolderName: str
    rootFolderPath: str
    ParentRootFolderName: str
    cwdfolderName: str

class AIGeneratedInfo(BaseModel):
    """AI-generated information about the project."""
    tags: List[str]
    app_name: Optional[str] = None
    app_description: Optional[str] = None

class ProjectEntry(BaseModel):
    """Project entry model for Cursor Project Manager."""
    name: str
    rootPath: str
    paths: List[str] = Field(default_factory=list)
    tags: List[str]
    enabled: bool = True
    project_uuid: Optional[str] = None

# -------------------- Custom Exceptions --------------------

class ConfigError(Exception):
    """Configuration error exception."""
    pass

class ProjectManagerError(Exception):
    """Project manager operation error."""
    pass

class AITaggingError(Exception):
    """AI tagging operation error."""
    pass

# -------------------- Logging Module --------------------
# TODO: Find out were the UTF char is coming from

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
        self.logger.info(f"  {'Tags:':<25} {', '.join(project_data.get('tags', []))}")
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

# -------------------- Project Context Module --------------------

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

# -------------------- AI Tagging Module --------------------

class AITaggingService:
    """Service for generating AI tags based on project content."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        
    def generate_tags(self, file_samples: Optional[Dict[str, str]]) -> Tuple[Optional[AIGeneratedInfo], Optional[Dict[str, Any]]]:
        """Uses OpenAI to generate tags, app name, and description based on file contents."""
        if not Config.OPENAI_API_KEY:
            self.logger.warning(colored("OpenAI API key not found. Set OPENAI_API_KEY in .env file to use AI tagging.", "yellow"))
            return None, None
            
        if not file_samples:
            return None, None
            
        try:
            # Prepare sample data for the API
            file_content_summary = "\n\n".join([f"Filename: {path}\n\n{content[:1000]}" 
                                              for path, content in file_samples.items()])
            
            # Prepare the API request
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {Config.OPENAI_API_KEY}"
            }
            
            payload = {
                "model": Config.OPENAI_MODEL,
                "messages": [
                    {
                        "role": "system", 
                        "content": "You are a helpful assistant that analyzes code repositories and generates descriptive information."
                    },
                    {
                        "role": "user",
                        "content": f"Analyze these files from a code repository and provide the following in JSON format:\n\n1. tags: 2-3 specific, descriptive tags that best categorize what this project is about\n2. app_name: A creative and appropriate name for this application\n3. app_description: A brief one-sentence description of what this application does\n\nRespond with ONLY a valid JSON object containing these three fields.\n\n{file_content_summary}"
                    }
                ],
                "temperature": Config.OPENAI_MODEL_TEMPERATURE
            }
            
            self.logger.info(colored("Contacting OpenAI for AI-generated project information...", "cyan"))
            response = requests.post(Config.OPENAI_API_URL, headers=headers, json=payload, timeout=30)
            
            if response.status_code != 200:
                self.logger.warning(colored(f"OpenAI API Error: {response.status_code} - {response.text}", "yellow"))
                return None, None
                
            api_response = response.json()
            response_text = api_response["choices"][0]["message"]["content"].strip()
            
            try:
                # Debug the raw response
                self.logger.debug(f"Raw API response text: {response_text}")
                
                # Try to parse as JSON - be more generous with JSON parsing
                # First, try to find if there's a JSON block in the response
                json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    self.logger.debug(f"Extracted JSON from markdown: {json_str}")
                    json_data = json.loads(json_str)
                else:
                    # Try to parse the whole response as JSON
                    json_data = json.loads(response_text)
                
                # Extract tags, app name and description from the response
                tags = json_data.get("tags", [])
                if isinstance(tags, str):
                    # Handle case where tags might be a comma-separated string
                    tags = [tag.strip().lower().replace(' ', '-') for tag in tags.split(',')]
                else:
                    # Handle case where tags is already a list
                    tags = [tag.strip().lower().replace(' ', '-') for tag in tags]
                
                # Limit to 3 tags
                tags = tags[:3]
                
                app_name = json_data.get("app_name")
                app_description = json_data.get("app_description")
                
                ai_info = AIGeneratedInfo(
                    tags=tags,
                    app_name=app_name,
                    app_description=app_description
                )
                
                self.logger.info(colored(f"✓ AI generated tags: {', '.join(tags)}", "green"))
                if app_name:
                    self.logger.info(colored(f"✓ AI generated app name: {app_name}", "green"))
                if app_description:
                    self.logger.info(colored(f"✓ AI generated description: {app_description}", "green"))
                    
                return ai_info, api_response
                
            except json.JSONDecodeError as e:
                # Fallback for non-JSON responses
                self.logger.warning(colored(f"AI response was not valid JSON: {str(e)}. Falling back to text parsing.", "yellow"))
                # Clean up the tags (remove quotes, split by comma, strip whitespace)
                tags = [tag.strip().lower().replace(' ', '-') for tag in response_text.split(',')]
                
                # Limit to 3 tags
                tags = tags[:3]
                
                ai_info = AIGeneratedInfo(tags=tags)
                self.logger.info(colored(f"✓ AI generated tags: {', '.join(tags)}", "green"))
                
                return ai_info, api_response
                
        except Exception as e:
            self.logger.warning(colored(f"Error generating AI information: {str(e)}", "yellow"))
            return None, None

# -------------------- Project Manager Module --------------------

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
            # Default tags - just parent folder name
            tags = [project_info.ParentRootFolderName.lower().replace(' ', '-')]
            
            # Add custom tag if provided
            if custom_tag:
                tags.append(custom_tag.lower().replace(' ', '-'))
            
            ai_generated_tags = []
            # Add AI-generated tags by default unless disabled
            if not skip_ai_tags:
                file_samples = project_context.get_file_samples()
                ai_info_model, api_response = ai_service.generate_tags(file_samples)
                if ai_info_model and ai_info_model.tags:
                    ai_generated_tags.extend(ai_info_model.tags) # These are already formatted
                    tags.extend(ai_generated_tags) # Add to main tags list
            
            # Use AI-generated app name if available, otherwise use folder name
            project_name = project_info.rootFolderName
            if ai_info_model and ai_info_model.app_name:
                project_name = ai_info_model.app_name
                self.logger.info(colored(f"✓ Using AI-generated name '{project_name}' for project entry", "green"))
                
            current_time_iso = datetime.now().isoformat()

            payload = {
                "uuid": project_uuid,
                "name": project_name,
                "root_path": project_info.rootFolderPath,
                "tags": list(set(tags)), # Ensure unique tags
                "ai_app_name": ai_info_model.app_name if ai_info_model else None,
                "ai_app_description": ai_info_model.app_description if ai_info_model else None,
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
            projects_data = db_manager.get_all_enabled_projects()
            
            cursor_project_entries = []
            for proj_dict in projects_data:
                # Map DB data to ProjectEntry Pydantic model
                # Assuming 'tags' in DB is JSON string, needs parsing
                db_tags_str = proj_dict.get('tags', '[]')
                try:
                    db_tags = json.loads(db_tags_str)
                except json.JSONDecodeError:
                    db_tags = [] # Default to empty list if JSON is invalid
                    self.logger.warning(f"Could not parse tags JSON from DB for {proj_dict.get('uuid')}: {db_tags_str}")

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

# -------------------- Database Manager Module --------------------

class DatabaseManager:
    """Manages SQLite database interactions."""
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self):
        """Establish SQLite connection."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row # Access columns by name
            logging.info(colored(f"✓ Connected to SQLite database at {self.db_path}", "green"))
        except sqlite3.Error as e:
            logging.error(colored(f"Error connecting to SQLite database: {e}", "red"))
            raise ProjectManagerError(f"Failed to connect to SQLite: {e}")

    def close(self):
        """Close SQLite connection."""
        if self.conn:
            self.conn.close()
            logging.info(colored("✓ SQLite connection closed.", "green"))

    def _execute_query(self, query: str, params: tuple = (), commit: bool = False, fetch_one: bool = False, fetch_all: bool = False):
        """Helper function to execute SQL queries."""
        if not self.conn:
            self.connect() # Should not happen if connect is called on init
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            
            if commit:
                self.conn.commit()
                return None # Or return cursor.lastrowid for inserts
            
            if fetch_one:
                return cursor.fetchone()
            
            if fetch_all:
                return cursor.fetchall()
            
            return None # For queries like CREATE TABLE or if no fetch/commit needed
        except sqlite3.Error as e:
            logging.error(colored(f"SQLite query error: {e}\nQuery: {query}\nParams: {params}", "red"))
            # Depending on severity, might re-raise or return None/False
            raise ProjectManagerError(f"SQLite error: {e}")


    def create_tables(self):
        """Create necessary tables if they don't exist."""
        create_projects_table_sql = """
        CREATE TABLE IF NOT EXISTS projects (
            uuid TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            root_path TEXT NOT NULL UNIQUE,
            tags TEXT, -- Store as JSON string
            ai_app_name TEXT,
            ai_app_description TEXT,
            date_added TEXT NOT NULL,
            last_updated TEXT NOT NULL,
            enabled INTEGER DEFAULT 1
        );
        """
        self._execute_query(create_projects_table_sql, commit=True)
        logging.info(colored("✓ Projects table checked/created.", "green"))

    def add_or_update_project(self, project_data: Dict[str, Any]):
        """Add a new project or update an existing one based on UUID."""
        # Ensure tags are stored as a JSON string
        if 'tags' in project_data and isinstance(project_data['tags'], list):
            project_data['tags'] = json.dumps(project_data['tags'])

        # Check if project exists to set date_added correctly
        existing_project = self.get_project_by_uuid(project_data['uuid'])
        if existing_project:
            project_data['date_added'] = existing_project['date_added'] # Keep original date_added
        else:
            project_data['date_added'] = datetime.now().isoformat() # New project

        project_data['last_updated'] = datetime.now().isoformat()

        # Fields for INSERT OR REPLACE. 'ai_tags_for_receipt' is not a DB field.
        db_fields = ['uuid', 'name', 'root_path', 'tags', 'ai_app_name', 
                     'ai_app_description', 'date_added', 'last_updated', 'enabled']
        
        columns = ', '.join(db_fields)
        placeholders = ', '.join(['?'] * len(db_fields))
        
        sql = f"INSERT OR REPLACE INTO projects ({columns}) VALUES ({placeholders});"
        
        values = tuple(project_data.get(field) for field in db_fields)
        
        self._execute_query(sql, values, commit=True)
        logging.info(colored(f"✓ Project '{project_data['name']}' (UUID: {project_data['uuid']}) saved to database.", "green"))

    def get_project_by_uuid(self, project_uuid: str) -> Optional[Dict[str, Any]]:
        """Fetch a project by its UUID."""
        sql = "SELECT * FROM projects WHERE uuid = ?;"
        row = self._execute_query(sql, (project_uuid,), fetch_one=True)
        return dict(row) if row else None

    def get_all_enabled_projects(self) -> List[Dict[str, Any]]:
        """Fetch all enabled projects from the database."""
        sql = "SELECT * FROM projects WHERE enabled = 1 ORDER BY name COLLATE NOCASE;"
        rows = self._execute_query(sql, fetch_all=True)
        return [dict(row) for row in rows]


# -------------------- Main Application --------------------

class Application:
    """Main application class."""
    
    def __init__(self, test_mode: bool = False):
        self.test_mode = test_mode
        self.project_uuid: Optional[str] = None
        self.db_manager = DatabaseManager(Config.SQLITE_DB_PATH)

        # Logging setup is deferred to run() after project_uuid might be known
        self.logging_manager = LoggingManager() 
        self.logger = None 
        self.log_file_path = None

        self.project_context = None # Initialized in run()
        self.ai_service = None      # Initialized in run()
        self.project_manager = None # Initialized in run()
        
    def _init_services(self):
        """Initialize services that depend on the logger."""
        if not self.logger:
            # This should not happen if setup_logging is called first
            raise RuntimeError("Logger not initialized before services.")
        self.project_context = ProjectContext(self.logger)
        self.ai_service = AITaggingService(self.logger)
        self.project_manager = ProjectManager(self.logger)

    def _handle_project_uuid(self):
        """Reads or generates and saves the project UUID."""
        uuid_file_path = Path.cwd() / Config.UUID_FILENAME
        try:
            if uuid_file_path.exists():
                read_uuid = uuid_file_path.read_text(encoding='utf-8').strip()
                # Validate UUID format
                try:
                    uuid.UUID(read_uuid)
                    self.project_uuid = read_uuid
                    # Logger is not set up yet, print for now or log later
                    print(colored(f"✓ Using existing Project ID: {self.project_uuid}", "cyan"))
                except ValueError:
                    print(colored(f"⚠️ Invalid UUID format in {Config.UUID_FILENAME}. A new ID will be generated.", "yellow"))
                    self.project_uuid = None # Fall through to generate new
            
            if not self.project_uuid and not self.test_mode: # Only generate if not found and not in test mode
                self.project_uuid = str(uuid.uuid4())
                uuid_file_path.write_text(self.project_uuid, encoding='utf-8')
                print(colored(f"✓ New Project ID generated and saved: {self.project_uuid} to {uuid_file_path}", "cyan"))
            elif not self.project_uuid and self.test_mode:
                # In test mode, if no file, generate for this run but don't save
                self.project_uuid = str(uuid.uuid4())
                print(colored(f"✓ TEST MODE: Using ephemeral Project ID for this run: {self.project_uuid}", "yellow"))

        except Exception as e:
            # Critical error if we can't manage UUID file
            print(colored(f"❌ Critical error handling project UUID file {uuid_file_path}: {e}", "red"))
            # Not raising here, will be caught by main error handler, but logging this early is good
            raise ProjectManagerError(f"Failed to handle project UUID file: {e}")


    def _setup_logging(self):
        """Sets up logging once project_uuid (or lack thereof for test) is determined."""
        self.logger, self.log_file_path = self.logging_manager.setup(
            test_mode=self.test_mode, 
            project_uuid=self.project_uuid if not self.test_mode else None
        )

    def parse_arguments(self) -> argparse.Namespace:
        """Parse command line arguments, excluding --test which is pre-parsed."""
        parser = argparse.ArgumentParser(description='Update Cursor Project Manager with current directory')
        # Add all arguments EXCEPT --test, as it's handled by main() for Application instantiation.
        parser.add_argument('--folder', action='store_true', help='Add "folder" suffix to the root folder name')
        parser.add_argument('--tag', type=str, help='Add a custom tag to the project')
        parser.add_argument('--skip-ai-tags', action='store_true', help='Skip AI tag generation (enabled by default)')
        # sys.argv[1:] will contain all args. We need to filter out --test if present.
        args_to_parse = [arg for arg in sys.argv[1:] if arg != '--test']
        return parser.parse_args(args_to_parse)

    def run(self) -> None:
        """Run the application."""
        # Initial print statements before logging is fully set up.
        print(colored("=== Cursor Project Updater (SQLite Edition) ===", "cyan"))

        if self.test_mode:
            print(colored("⚠️ Running in TEST MODE - No changes will be saved to DB or .pyprojectid", "yellow"))
        
        try:
            # 1. Handle Project UUID (reads or generates)
            self._handle_project_uuid()

            # 2. Setup Logging (uses project_uuid if available and not test_mode)
            self._setup_logging() # Now self.logger is available

            # 3. Initialize services that depend on the logger
            self._init_services()

            # 4. Validate configuration (can now use self.logger)
            Config.validate() # This mainly checks for PROJECTS_FILE, might need adjustment
            
            # 5. Connect to Database and create tables
            self.db_manager.connect()
            self.db_manager.create_tables() # Ensures tables exist

            # 6. Parse arguments
            args = self.parse_arguments() # self.logger is available for this method if it logs
            
            # 7. Get project information (local context)
            project_info_model = self.project_context.get_project_info(args.folder)
            
            # 8. Create project data payload (includes AI tagging if not skipped)
            project_data_payload, api_response = self.project_manager.create_project_payload(
                project_uuid=self.project_uuid, # Should be set by _handle_project_uuid
                project_info=project_info_model,
                ai_service=self.ai_service,
                project_context=self.project_context,
                custom_tag=args.tag,
                skip_ai_tags=args.skip_ai_tags
            )
            
            # 9. Update database unless in test mode
            if not self.test_mode:
                self.db_manager.add_or_update_project(project_data_payload)
                self.logger.info(colored("✓ Project data saved to SQLite database!", "green"))
                
                # 10. Regenerate projects.json for Cursor Project Manager
                self.project_manager.regenerate_cursor_projects_json(self.db_manager)
            else:
                self.logger.info(colored("✓ Test successful! Project data generated but not saved to DB or projects.json.", "green"))
            
            # 11. Write receipt to log
            # Use project_data_payload for the receipt as it contains all relevant info including what would be DB state
            self.logging_manager.write_receipt(project_data_payload, api_response)
            
            # Print log file location
            self.logger.info(colored(f"Log file is at: {os.path.abspath(self.log_file_path)}", "cyan"))
            # Also print to console as logger might not show this if level is higher
            print(colored(f"Log file is at: {os.path.abspath(self.log_file_path)}", "cyan"))

        except (ConfigError, ProjectManagerError, AITaggingError) as e:
            if self.logger:
                self.logger.error(colored(f"Error: {str(e)}", "red"), exc_info=True)
            else:
                print(colored(f"Error: {str(e)}", "red"))
            sys.exit(1)
        except Exception as e:
            if self.logger:
                self.logger.error(colored(f"Unexpected error: {str(e)}", "red"), exc_info=True)
            else:
                print(colored(f"Unexpected error: {str(e)}", "red"))
            sys.exit(1)
        finally:
            if self.db_manager:
                self.db_manager.close()

# -------------------- Script Entry Point --------------------

def main():
    """Main function to run the project updater."""
    # Pre-parse only the --test argument to determine test_mode for Application instantiation
    test_mode_parser = argparse.ArgumentParser(add_help=False) # Suppress help for this pre-parser
    test_mode_parser.add_argument('--test', action='store_true', default=False)
    test_args, _ = test_mode_parser.parse_known_args() # Consumes --test if present
    
    app = Application(test_mode=test_args.test)
    app.run()

if __name__ == "__main__":
    main() 