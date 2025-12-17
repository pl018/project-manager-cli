"""Main application module for the project manager CLI."""

import argparse
import os
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv
from termcolor import colored

from core.config_manager import config as Config, ConfigManager
from core.exceptions import ConfigError, ProjectManagerError, AITaggingError
from core.database import DatabaseManager
from .services import (
    LoggingManager,
    AITaggingService,
    ProjectContext,
    ProjectManager
)

# Load environment variables from .env file
load_dotenv()


class Application:
    """Main application class."""
    
    def __init__(self, test_mode: bool = False) -> None:
        self.test_mode = test_mode
        self.project_uuid: str = None
        self.db_manager = DatabaseManager(Config.SQLITE_DB_PATH)

        # Logging setup is deferred to run() after project_uuid might be known
        self.logging_manager = LoggingManager() 
        self.logger = None 
        self.log_file_path = None

        self.project_context = None # Initialized in run()
        self.ai_service = None      # Initialized in run()
        self.project_manager = None # Initialized in run()
        
    def _init_services(self) -> None:
        """Initialize services that depend on the logger."""
        if not self.logger:
            # This should not happen if setup_logging is called first
            raise RuntimeError("Logger not initialized before services.")
        self.project_context = ProjectContext(self.logger)
        self.ai_service = AITaggingService(self.logger)
        self.project_manager = ProjectManager(self.logger)

    def _handle_project_uuid(self) -> None:
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


    def _setup_logging(self) -> None:
        """Sets up logging once project_uuid (or lack thereof for test) is determined."""
        self.logger, self.log_file_path = self.logging_manager.setup(
            test_mode=self.test_mode, 
            project_uuid=self.project_uuid if not self.test_mode else None
        )

    def parse_arguments(self, args_list: list = None) -> argparse.Namespace:
        """Parse command line arguments, excluding --test which is pre-parsed."""
        parser = argparse.ArgumentParser(description='Update Cursor Project Manager with current directory')
        # Add all arguments EXCEPT --test, as it's handled by main() for Application instantiation.
        parser.add_argument('--folder', action='store_true', help='Add "folder" suffix to the root folder name')
        parser.add_argument('--tag', type=str, help='Add a custom tag (one-word lowercase alphanumeric)')
        parser.add_argument('--skip-ai-tags', action='store_true', help='Skip AI tag generation (enabled by default)')
        
        # Use provided args_list or default to empty list when called from CLI
        if args_list is None:
            args_list = []
        
        return parser.parse_args(args_list)

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