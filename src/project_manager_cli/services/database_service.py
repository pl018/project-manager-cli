"""Database service for the project manager CLI."""

import json
import logging
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional

from termcolor import colored

from ..exceptions import ProjectManagerError


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
        # Ensure tags are stored as a JSON string without mutating original dict
        tags_value = project_data.get('tags')
        if isinstance(tags_value, list):
            tags_as_json = json.dumps(tags_value)
        elif isinstance(tags_value, str):
            # Assume it might already be JSON; if not, wrap as list
            try:
                parsed = json.loads(tags_value)
                tags_as_json = json.dumps(parsed)
            except Exception:
                tags_as_json = json.dumps([t.strip() for t in tags_value.split(',') if t.strip()])
        else:
            tags_as_json = json.dumps([])

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
        
        # Build values tuple using computed tags JSON
        values_map = dict(project_data)
        values_map['tags'] = tags_as_json
        values = tuple(values_map.get(field) for field in db_fields)
        
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