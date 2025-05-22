#!/usr/bin/env python3

import json
import os
import sys
import argparse
import glob
import re
import logging
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
    EXCLUDE_DIRS = ['node_modules', 'venv', '.git', '__pycache__', 'dist', 'build', 'target']
    IMPORTANT_EXTENSIONS = ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs', '.c', '.cpp', 
                           '.h', '.cs', '.php', '.rb', '.md', '.html', '.css', '.json', '.yml', '.yaml']
                           
    # API Configuration
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
    OPENAI_MODEL = "o4-mini"
    OPENAI_MODEL_TEMPERATURE = 1
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration."""
        if not os.path.exists(cls.PROJECTS_FILE):
            raise ConfigError(f"Projects file not found at {cls.PROJECTS_FILE}")
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
        
    def setup(self, test_mode: bool = False) -> Tuple[logging.Logger, str]:
        """Configure logging to write to both console and a log file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = "test_" if test_mode else "pyproject_log_"
        log_file = f"{prefix}{timestamp}.log"
        
        # Create logger
        logger = logging.getLogger('pyproject')
        logger.setLevel(logging.INFO)
        
        # Prevent duplicate handlers if setup is called multiple times
        if logger.handlers:
            return logger, log_file
            
        # Create file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        self.logger = logger
        self.log_file_path = log_file
        
        return logger, log_file
        
    def write_receipt(self, api_response: Optional[Dict[str, Any]], project_entry: ProjectEntry, ai_info: Optional[AIGeneratedInfo] = None) -> None:
        """Write a detailed receipt to the log file."""
        if not self.logger:
            return

        # Use a consistent border style
        border = "=" * 60
        section_break = "-" * 60

        self.logger.info(f"\\n{border}")
        self.logger.info(f"{'PROJECT MANAGER RECEIPT':^60}")
        self.logger.info(f"{border}\\n")
        
        # Project information
        self.logger.info(f"  {'Project Name:':<25} {project_entry.name}")
        self.logger.info(f"  {'Project Path:':<25} {project_entry.rootPath}")
        self.logger.info(f"  {'Tags:':<25} {', '.join(project_entry.tags)}")
        self.logger.info(f"  {'Added to Project Manager:':<25} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # AI-generated information if available
        if ai_info:
            self.logger.info(f"\\n{section_break}")
            self.logger.info(f"{'AI GENERATED INFORMATION':^60}")
            self.logger.info(f"{section_break}\\n")
            self.logger.info(f"  {'AI Tags:':<25} {', '.join(ai_info.tags) if ai_info.tags else 'None'}")
            if ai_info.app_name:
                # Indicate if the AI-generated name was used
                name_status = "(Used as project name)" if project_entry.name == ai_info.app_name else ""
                self.logger.info(f"  {'AI App Name:':<25} {ai_info.app_name} {name_status}")
            if ai_info.app_description:
                self.logger.info(f"  {'AI App Description:':<25} {ai_info.app_description}")
        
        # API response information if available
        if api_response:
            self.logger.info(f"\\n{section_break}")
            self.logger.info(f"{'AI TAG GENERATION DETAILS':^60}")
            self.logger.info(f"{section_break}\\n")
            self.logger.info(f"  {'Model:':<25} {api_response.get('model', 'N/A')}")
            
            # Format the raw response nicely
            raw_content_str = api_response['choices'][0]['message']['content']
            try:
                # Attempt to parse and pretty-print if it's JSON
                raw_content_json = json.loads(raw_content_str)
                pretty_raw_content = json.dumps(raw_content_json, indent=2)
                self.logger.info(f"  {'Raw Response:':<25}\\n{pretty_raw_content}")
            except json.JSONDecodeError:
                # If not JSON, print as is
                self.logger.info(f"  {'Raw Response:':<25} {raw_content_str}")
            
            self.logger.info(f"  {'Token Usage:':<25} {api_response.get('usage', {}).get('total_tokens', 'N/A')} total tokens")
        
        self.logger.info(f"\\n  {'Log file location:':<25} {os.path.abspath(self.log_file_path)}")
        self.logger.info(f"{border}\\n")

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
        
    def create_project_entry(self, 
                            project_info: ProjectInfo, 
                            ai_service: AITaggingService,
                            project_context: ProjectContext,
                            custom_tag: Optional[str] = None, 
                            skip_ai_tags: bool = False) -> Tuple[ProjectEntry, Optional[Dict[str, Any]], Optional[AIGeneratedInfo]]:
        """Create project entry in JSON format."""
        api_response = None
        ai_info = None
        try:
            # Default tags - just parent folder name
            tags = [
                project_info.ParentRootFolderName
            ]
            
            # Add custom tag if provided
            if custom_tag:
                tags.append(custom_tag)
            
            # Add AI-generated tags by default unless disabled
            if not skip_ai_tags:
                file_samples = project_context.get_file_samples()
                ai_info, api_response = ai_service.generate_tags(file_samples)
                if ai_info and ai_info.tags:
                    tags.extend(ai_info.tags)
            
            # Use AI-generated app name if available, otherwise use folder name
            project_name = project_info.rootFolderName
            if ai_info and ai_info.app_name:
                project_name = ai_info.app_name
                self.logger.info(colored(f"✓ Using AI-generated name '{project_name}' for project entry", "green"))
                
            # Create the project entry with the selected name
            entry = ProjectEntry(
                name=project_name,
                rootPath=project_info.rootFolderPath,
                paths=[],
                tags=tags
            )
            
            self.logger.info(colored("✓ Project entry created successfully", "green"))
            self.logger.info(colored(f"✓ Project name set to: {entry.name}", "green"))
            
            return entry, api_response, ai_info
        except Exception as e:
            self.logger.error(colored(f"Error creating project entry: {str(e)}", "red"))
            raise ProjectManagerError(f"Failed to create project entry: {str(e)}")

    def update_projects_file(self, new_entry: ProjectEntry) -> None:
        """Update the projects.json file with the new entry."""
        try:
            # Check if file exists (should be handled by Config.validate(), but double-checking)
            if not os.path.exists(Config.PROJECTS_FILE):
                raise ProjectManagerError(f"Projects file not found at {Config.PROJECTS_FILE}")

            # Read existing content
            with open(Config.PROJECTS_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
                try:
                    projects = json.loads(content)
                except json.JSONDecodeError:
                    raise ProjectManagerError("Invalid JSON in projects file")

            # Add new entry
            if not isinstance(projects, list):
                raise ProjectManagerError("Projects file does not contain a valid array")

            projects.append(new_entry.dict())

            # Write updated content
            with open(Config.PROJECTS_FILE, 'w', encoding='utf-8') as f:
                json.dump(projects, f, indent=4)

            self.logger.info(colored("✓ Projects file updated successfully", "green"))
            
            # Validate the updated file
            with open(Config.PROJECTS_FILE, 'r', encoding='utf-8') as f:
                json.load(f)
            self.logger.info(colored("✓ JSON validation successful", "green"))

        except Exception as e:
            self.logger.error(colored(f"Error updating projects file: {str(e)}", "red"))
            raise ProjectManagerError(f"Failed to update projects file: {str(e)}")

# -------------------- Main Application --------------------

class Application:
    """Main application class."""
    
    def __init__(self, test_mode: bool = False):
        self.test_mode = test_mode
        self.logging_manager = LoggingManager()
        self.logger, self.log_file_path = self.logging_manager.setup(test_mode)
        self.project_context = ProjectContext(self.logger)
        self.ai_service = AITaggingService(self.logger)
        self.project_manager = ProjectManager(self.logger)
        
    def parse_arguments(self) -> argparse.Namespace:
        """Parse command line arguments."""
        parser = argparse.ArgumentParser(description='Update Cursor Project Manager with current directory')
        parser.add_argument('--folder', action='store_true', help='Add "folder" suffix to the root folder name')
        parser.add_argument('--tag', type=str, help='Add a custom tag to the project')
        parser.add_argument('--skip-ai-tags', action='store_true', help='Skip AI tag generation (enabled by default)')
        parser.add_argument('--test', action='store_true', help='Run in test mode without updating projects.json')
        return parser.parse_args()
        
    def run(self) -> None:
        """Run the application."""
        self.logger.info(colored("\n=== Cursor Project Updater ===\n", "cyan"))
        
        if self.test_mode:
            self.logger.info(colored("⚠️ Running in TEST MODE - No changes will be saved to projects.json", "yellow"))
        
        try:
            # Validate configuration
            Config.validate()
            
            # Parse arguments
            args = self.parse_arguments()
            
            # Get project information
            project_info = self.project_context.get_project_info(args.folder)
            
            # Create project entry
            new_entry, api_response, ai_info = self.project_manager.create_project_entry(
                project_info, 
                self.ai_service,
                self.project_context,
                args.tag, 
                args.skip_ai_tags
            )
            
            # Update projects file unless in test mode
            if not self.test_mode:
                self.project_manager.update_projects_file(new_entry)
                self.logger.info(colored("\n✓ Project successfully added to Cursor Project Manager!", "green"))
            else:
                self.logger.info(colored("\n✓ Test successful! Project entry generated but not added to Cursor Project Manager.", "green"))
            
            # Write receipt
            self.logging_manager.write_receipt(api_response, new_entry, ai_info)
            
            # Print log file location
            print(colored(f"\nLog file created at: {os.path.abspath(self.log_file_path)}", "cyan"))
            
        except (ConfigError, ProjectManagerError, AITaggingError) as e:
            self.logger.error(colored(f"\nError: {str(e)}", "red"))
            sys.exit(1)
        except Exception as e:
            self.logger.error(colored(f"\nUnexpected error: {str(e)}", "red"))
            sys.exit(1)

# -------------------- Script Entry Point --------------------

def main():
    """Main function to run the project updater."""
    # Parse args first to check for test mode
    parser = argparse.ArgumentParser(description='Update Cursor Project Manager with current directory')
    parser.add_argument('--test', action='store_true', help='Run in test mode without updating projects.json')
    args, _ = parser.parse_known_args()
    
    app = Application(test_mode=args.test)
    app.run()

if __name__ == "__main__":
    main() 