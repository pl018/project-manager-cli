"""Enhanced SQLite database manager with support for notes, favorites, and tags."""

from contextlib import contextmanager
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import Config
from .exceptions import DatabaseError
from .models import Project, Tag, ToolConfig


class DatabaseManager:
    """Manages SQLite database interactions with enhanced features."""

    # Current schema version - increment this when adding new columns/tables
    SCHEMA_VERSION = 2

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or Config.SQLITE_DB_PATH
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self) -> None:
        """Establish SQLite connection."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            # Auto-migrate schema on connection
            self._migrate_schema()
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to connect to database: {e}")

    def close(self) -> None:
        """Close SQLite connection."""
        if self.conn:
            self.conn.close()

    @contextmanager
    def transaction(self):
        """
        Context manager for database transactions with automatic commit/rollback.

        Provides ACID guarantees for database operations. All database modifications
        within the context are committed atomically, or rolled back if any error occurs.

        Usage:
            with db.transaction():
                db.archive_project(...)
                db.update_project_fields(...)
                # Multiple DB operations executed atomically
                # If any operation raises an exception, ALL changes are rolled back

        Important notes:
        - Only database operations can be part of the transaction
        - File system operations (creating files, deleting directories) cannot be
          rolled back by SQLite and should be handled separately with cleanup logic
        - For multi-step operations involving both DB and file operations, structure
          your code to allow cleanup of file operations if DB transaction fails

        Example pattern for file + DB operations:
            # 1. Perform file operation
            archive_path = create_zip_archive(project_path)
            try:
                # 2. Update database in transaction
                with db.transaction():
                    db.archive_project(uuid, archive_path, size)
            except Exception:
                # 3. Clean up file if DB operation failed
                if archive_path.exists():
                    archive_path.unlink()
                raise
        """
        if not self.conn:
            self.connect()

        try:
            # Begin transaction
            yield self.conn
            # Commit on successful completion
            self.conn.commit()
        except Exception:
            # Rollback on any error
            self.conn.rollback()
            raise

    def _execute_query(
        self,
        query: str,
        params: tuple = (),
        commit: bool = False,
        fetch_one: bool = False,
        fetch_all: bool = False
    ):
        """Execute SQL queries with error handling."""
        if not self.conn:
            self.connect()

        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)

            if commit:
                self.conn.commit()
                return cursor.lastrowid

            if fetch_one:
                return cursor.fetchone()

            if fetch_all:
                return cursor.fetchall()

            return None
        except sqlite3.Error as e:
            raise DatabaseError(f"SQLite error: {e}\nQuery: {query}")

    def create_tables(self) -> None:
        """Create all necessary tables."""

        # Schema version tracking table
        create_schema_version_sql = """
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL
        );
        """

        # Enhanced projects table
        create_projects_sql = """
        CREATE TABLE IF NOT EXISTS projects (
            uuid TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            root_path TEXT NOT NULL UNIQUE,
            tags TEXT,
            ai_app_name TEXT,
            ai_app_description TEXT,
            description TEXT,
            notes TEXT,
            favorite INTEGER DEFAULT 0,
            last_opened TEXT,
            open_count INTEGER DEFAULT 0,
            date_added TEXT NOT NULL,
            last_updated TEXT NOT NULL,
            enabled INTEGER DEFAULT 1,
            color_theme TEXT DEFAULT 'blue'
        );
        """

        # Tags table for managing available tags
        create_tags_sql = """
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            color TEXT DEFAULT '#3b82f6',
            icon TEXT DEFAULT '🏷️'
        );
        """

        # Tool configurations table
        create_tool_configs_sql = """
        CREATE TABLE IF NOT EXISTS tool_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_uuid TEXT NOT NULL,
            tool_name TEXT NOT NULL,
            config TEXT,
            FOREIGN KEY (project_uuid) REFERENCES projects(uuid) ON DELETE CASCADE,
            UNIQUE(project_uuid, tool_name)
        );
        """

        # Search history table
        create_search_history_sql = """
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            filters TEXT,
            timestamp TEXT NOT NULL
        );
        """

        self._execute_query(create_schema_version_sql, commit=True)
        self._execute_query(create_projects_sql, commit=True)
        self._execute_query(create_tags_sql, commit=True)
        self._execute_query(create_tool_configs_sql, commit=True)
        self._execute_query(create_search_history_sql, commit=True)

        # Initialize default tags
        self._initialize_default_tags()

    def _initialize_default_tags(self) -> None:
        """Initialize default tags from config."""
        for tag_name, tag_data in Config.DEFAULT_TAGS.items():
            sql = """
            INSERT OR IGNORE INTO tags (name, color, icon)
            VALUES (?, ?, ?);
            """
            self._execute_query(
                sql,
                (tag_name, tag_data['color'], tag_data['icon']),
                commit=True
            )

    def _get_current_schema_version(self) -> int:
        """Get the current schema version from the database."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
            row = cursor.fetchone()
            return row[0] if row else 0
        except sqlite3.OperationalError:
            # schema_version table doesn't exist yet
            return 0

    def _set_schema_version(self, version: int) -> None:
        """Record the current schema version."""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO schema_version (version, applied_at) VALUES (?, ?)",
            (version, datetime.now().isoformat())
        )
        self.conn.commit()

    def _migrate_schema(self) -> None:
        """
        Automatically migrate database schema to add missing columns.

        This method uses a versioning system to track schema changes and only
        runs migrations when the database version is behind the code version.
        """
        if not self.conn:
            return

        try:
            cursor = self.conn.cursor()

            # Check if projects table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='projects'"
            )
            if not cursor.fetchone():
                # Table doesn't exist yet, will be created by create_tables()
                return

            # Get current schema version
            current_version = self._get_current_schema_version()

            # If already at latest version, skip migration
            if current_version >= self.SCHEMA_VERSION:
                return

            # Get existing columns
            cursor.execute("PRAGMA table_info(projects)")
            existing_columns = {row[1] for row in cursor.fetchall()}

            # Define required columns with their SQL definitions (version 1)
            required_columns_v1 = {
                'description': 'TEXT',
                'notes': 'TEXT',
                'favorite': 'INTEGER DEFAULT 0',
                'last_opened': 'TEXT',
                'open_count': 'INTEGER DEFAULT 0',
                'color_theme': "TEXT DEFAULT 'blue'",
            }

            # Version 2: Archive support
            required_columns_v2 = {
                'archived': 'INTEGER DEFAULT 0',
                'archive_path': 'TEXT',
                'archive_date': 'TEXT',
                'archive_size_mb': 'REAL',
            }

            # Apply migrations in order
            migrations_applied = []

            if current_version < 1:
                # Apply version 1 migrations
                for column_name, column_def in required_columns_v1.items():
                    if column_name not in existing_columns:
                        try:
                            cursor.execute(
                                f"ALTER TABLE projects ADD COLUMN {column_name} {column_def}"
                            )
                            migrations_applied.append(f"Added column: {column_name}")
                        except sqlite3.Error as e:
                            # Log error but continue with other migrations
                            print(f"Warning: Failed to add column {column_name}: {e}")

            if current_version < 2:
                # Apply version 2 migrations
                # Refresh column list after v1 migrations
                cursor.execute("PRAGMA table_info(projects)")
                existing_columns = {row[1] for row in cursor.fetchall()}

                for column_name, column_def in required_columns_v2.items():
                    if column_name not in existing_columns:
                        try:
                            cursor.execute(
                                f"ALTER TABLE projects ADD COLUMN {column_name} {column_def}"
                            )
                            migrations_applied.append(f"Added column: {column_name}")
                        except sqlite3.Error as e:
                            print(f"Warning: Failed to add column {column_name}: {e}")

            # Commit all migrations
            if migrations_applied:
                self.conn.commit()
                print(f"Applied {len(migrations_applied)} schema migrations")

            # Update schema version
            self._set_schema_version(self.SCHEMA_VERSION)

        except sqlite3.Error as e:
            # Log migration failure but don't crash the app
            print(f"Warning: Schema migration failed: {e}")
            # The app will handle missing columns gracefully

    # ==================== Project Operations ====================

    def add_or_update_project(self, project_data: Dict[str, Any]) -> str:
        """Add or update a project."""
        # Convert tags list to JSON string
        if 'tags' in project_data and isinstance(project_data['tags'], list):
            project_data['tags'] = json.dumps(project_data['tags'])

        # Check if project exists
        existing = self.get_project_by_uuid(project_data['uuid'])

        if existing:
            # Preserve certain fields on update
            project_data['date_added'] = existing['date_added']
            project_data['open_count'] = existing.get('open_count', 0)
            if 'favorite' not in project_data:
                project_data['favorite'] = existing.get('favorite', 0)
        else:
            # New project defaults
            project_data['date_added'] = datetime.now().isoformat()
            project_data['open_count'] = 0
            if 'favorite' not in project_data:
                project_data['favorite'] = 0

        project_data['last_updated'] = datetime.now().isoformat()

        # Database fields
        db_fields = [
            'uuid', 'name', 'root_path', 'tags', 'ai_app_name',
            'ai_app_description', 'description', 'notes', 'favorite', 'last_opened',
            'open_count', 'date_added', 'last_updated', 'enabled', 'color_theme'
        ]

        columns = ', '.join(db_fields)
        placeholders = ', '.join(['?'] * len(db_fields))

        sql = f"INSERT OR REPLACE INTO projects ({columns}) VALUES ({placeholders});"
        values = tuple(project_data.get(field) for field in db_fields)

        self._execute_query(sql, values, commit=True)
        return project_data['uuid']

    def get_project_by_uuid(self, project_uuid: str) -> Optional[Dict[str, Any]]:
        """Fetch a project by UUID."""
        sql = "SELECT * FROM projects WHERE uuid = ?;"
        row = self._execute_query(sql, (project_uuid,), fetch_one=True)

        if row:
            project = dict(row)
            # Parse tags JSON
            if project.get('tags'):
                try:
                    project['tags'] = json.loads(project['tags'])
                except json.JSONDecodeError:
                    project['tags'] = []
            return project
        return None

    def get_project_by_path(self, root_path: str) -> Optional[Dict[str, Any]]:
        """Fetch a project by root path."""
        sql = "SELECT * FROM projects WHERE root_path = ?;"
        row = self._execute_query(sql, (root_path,), fetch_one=True)

        if row:
            project = dict(row)
            if project.get('tags'):
                try:
                    project['tags'] = json.loads(project['tags'])
                except json.JSONDecodeError:
                    project['tags'] = []
            return project
        return None

    def get_all_projects(self, enabled_only: bool = True) -> List[Dict[str, Any]]:
        """Fetch all projects."""
        if enabled_only:
            sql = "SELECT * FROM projects WHERE enabled = 1 AND archived = 0 ORDER BY name COLLATE NOCASE;"
        else:
            sql = "SELECT * FROM projects ORDER BY name COLLATE NOCASE;"

        rows = self._execute_query(sql, fetch_all=True)
        projects = []

        for row in rows:
            project = dict(row)
            if project.get('tags'):
                try:
                    project['tags'] = json.loads(project['tags'])
                except json.JSONDecodeError:
                    project['tags'] = []
            projects.append(project)

        return projects

    # Backward-compatibility helpers (older CLI layers used these names)
    def get_all_enabled_projects(self) -> List[Dict[str, Any]]:
        """Fetch all enabled projects (backward compatible alias)."""
        return self.get_all_projects(enabled_only=True)

    def search_projects(self, query: str = "", tags: List[str] = None,
                       favorites_only: bool = False) -> List[Dict[str, Any]]:
        """Search projects with filters."""
        conditions = ["enabled = 1"]
        params = []

        if query:
            # Check if notes column exists to build appropriate query
            try:
                cursor = self.conn.cursor()
                cursor.execute("PRAGMA table_info(projects)")
                columns = [row[1] for row in cursor.fetchall()]
                has_notes = 'notes' in columns
                has_description = 'description' in columns
            except sqlite3.Error:
                has_notes = False
                has_description = False
            
            if has_notes and has_description:
                conditions.append("(name LIKE ? OR root_path LIKE ? OR description LIKE ? OR notes LIKE ?)")
                search_term = f"%{query}%"
                params.extend([search_term, search_term, search_term, search_term])
            elif has_description:
                conditions.append("(name LIKE ? OR root_path LIKE ? OR description LIKE ?)")
                search_term = f"%{query}%"
                params.extend([search_term, search_term, search_term])
            elif has_notes:
                conditions.append("(name LIKE ? OR root_path LIKE ? OR notes LIKE ?)")
                search_term = f"%{query}%"
                params.extend([search_term, search_term, search_term])
            else:
                conditions.append("(name LIKE ? OR root_path LIKE ?)")
                search_term = f"%{query}%"
                params.extend([search_term, search_term])

        if favorites_only:
            # Check if favorite column exists
            try:
                cursor = self.conn.cursor()
                cursor.execute("PRAGMA table_info(projects)")
                columns = [row[1] for row in cursor.fetchall()]
                has_favorite = 'favorite' in columns
            except sqlite3.Error:
                has_favorite = False
            
            if has_favorite:
                conditions.append("favorite = 1")
            else:
                # No favorites column - return empty results for favorites filter
                return []

        sql = f"SELECT * FROM projects WHERE {' AND '.join(conditions)} ORDER BY name COLLATE NOCASE;"
        rows = self._execute_query(sql, tuple(params), fetch_all=True)

        projects = []
        for row in rows:
            project = dict(row)
            if project.get('tags'):
                try:
                    project['tags'] = json.loads(project['tags'])
                except json.JSONDecodeError:
                    project['tags'] = []

            # Filter by tags if specified
            if tags:
                if not any(tag in project.get('tags', []) for tag in tags):
                    continue

            projects.append(project)

        return projects

    def toggle_favorite(self, project_uuid: str) -> bool:
        """Toggle favorite status of a project."""
        project = self.get_project_by_uuid(project_uuid)
        if not project:
            return False

        new_favorite = 0 if project.get('favorite', 0) == 1 else 1
        sql = "UPDATE projects SET favorite = ?, last_updated = ? WHERE uuid = ?;"
        self._execute_query(
            sql,
            (new_favorite, datetime.now().isoformat(), project_uuid),
            commit=True
        )
        return new_favorite == 1

    def update_notes(self, project_uuid: str, notes: str) -> bool:
        """Update project notes."""
        sql = "UPDATE projects SET notes = ?, last_updated = ? WHERE uuid = ?;"
        self._execute_query(
            sql,
            (notes, datetime.now().isoformat(), project_uuid),
            commit=True
        )
        return True

    def update_project_fields(self, project_uuid: str, **fields) -> bool:
        """Update specific project fields (ai_app_name, description, tags)."""
        project = self.get_project_by_uuid(project_uuid)
        if not project:
            raise DatabaseError(f"Project with UUID {project_uuid} not found")

        # Build update statement dynamically based on provided fields
        allowed_fields = ['ai_app_name', 'description', 'tags']
        updates = []
        params = []

        for field, value in fields.items():
            if field in allowed_fields:
                if field == 'tags':
                    # Serialize tags as JSON
                    value = json.dumps(value) if isinstance(value, list) else value
                updates.append(f"{field} = ?")
                params.append(value)

        if not updates:
            return False

        # Always update last_updated timestamp
        updates.append("last_updated = ?")
        params.append(datetime.now().isoformat())
        params.append(project_uuid)

        sql = f"UPDATE projects SET {', '.join(updates)} WHERE uuid = ?;"
        self._execute_query(sql, tuple(params), commit=True)
        return True

    def record_project_open(self, project_uuid: str) -> bool:
        """Record that a project was opened."""
        sql = """
        UPDATE projects
        SET last_opened = ?, open_count = open_count + 1, last_updated = ?
        WHERE uuid = ?;
        """
        now = datetime.now().isoformat()
        self._execute_query(sql, (now, now, project_uuid), commit=True)
        return True

    def delete_project(self, project_uuid: str) -> bool:
        """Delete a project (soft delete by setting enabled = 0)."""
        sql = "UPDATE projects SET enabled = 0, last_updated = ? WHERE uuid = ?;"
        self._execute_query(
            sql,
            (datetime.now().isoformat(), project_uuid),
            commit=True
        )
        return True

    def hard_delete_project(self, project_uuid: str) -> bool:
        """Permanently delete a project."""
        sql = "DELETE FROM projects WHERE uuid = ?;"
        self._execute_query(sql, (project_uuid,), commit=True)
        return True

    def archive_project(
        self,
        project_uuid: str,
        archive_path: str,
        archive_size_mb: float
    ) -> bool:
        """
        Mark project as archived and store archive metadata.

        Args:
            project_uuid: UUID of project
            archive_path: Full path to archive ZIP file
            archive_size_mb: Size of archive in megabytes

        Returns:
            True if successful
        """
        sql = """
        UPDATE projects
        SET archived = 1,
            archive_path = ?,
            archive_date = ?,
            archive_size_mb = ?,
            last_updated = ?
        WHERE uuid = ?;
        """
        now = datetime.now().isoformat()
        self._execute_query(
            sql,
            (archive_path, now, archive_size_mb, now, project_uuid),
            commit=True
        )
        return True

    def get_archived_projects(self) -> List[Dict[str, Any]]:
        """Fetch all archived projects."""
        sql = "SELECT * FROM projects WHERE archived = 1 ORDER BY archive_date DESC;"
        rows = self._execute_query(sql, fetch_all=True)
        projects = []

        for row in rows:
            project = dict(row)
            if project.get('tags'):
                try:
                    project['tags'] = json.loads(project['tags'])
                except json.JSONDecodeError:
                    project['tags'] = []
            projects.append(project)

        return projects

    # ==================== Tag Operations ====================

    def get_all_tags(self) -> List[Dict[str, Any]]:
        """Get all available tags."""
        sql = "SELECT * FROM tags ORDER BY name COLLATE NOCASE;"
        rows = self._execute_query(sql, fetch_all=True)
        return [dict(row) for row in rows]

    def add_tag(self, name: str, color: str = "#3b82f6", icon: str = "🏷️") -> int:
        """Add a new tag."""
        sql = "INSERT OR IGNORE INTO tags (name, color, icon) VALUES (?, ?, ?);"
        return self._execute_query(sql, (name, color, icon), commit=True)

    def update_tag(self, name: str, color: str = None, icon: str = None) -> bool:
        """Update tag properties."""
        updates = []
        params = []

        if color:
            updates.append("color = ?")
            params.append(color)
        if icon:
            updates.append("icon = ?")
            params.append(icon)

        if not updates:
            return False

        params.append(name)
        sql = f"UPDATE tags SET {', '.join(updates)} WHERE name = ?;"
        self._execute_query(sql, tuple(params), commit=True)
        return True

    # ==================== Tool Config Operations ====================

    def set_tool_config(self, project_uuid: str, tool_name: str, config: dict) -> bool:
        """Set tool configuration for a project."""
        config_json = json.dumps(config)
        sql = """
        INSERT OR REPLACE INTO tool_configs (project_uuid, tool_name, config)
        VALUES (?, ?, ?);
        """
        self._execute_query(sql, (project_uuid, tool_name, config_json), commit=True)
        return True

    def get_tool_config(self, project_uuid: str, tool_name: str) -> Optional[dict]:
        """Get tool configuration for a project."""
        sql = "SELECT config FROM tool_configs WHERE project_uuid = ? AND tool_name = ?;"
        row = self._execute_query(sql, (project_uuid, tool_name), fetch_one=True)

        if row and row['config']:
            try:
                return json.loads(row['config'])
            except json.JSONDecodeError:
                return None
        return None

    # ==================== Statistics ====================

    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        stats = {}

        # Total projects
        sql = "SELECT COUNT(*) as count FROM projects WHERE enabled = 1;"
        row = self._execute_query(sql, fetch_one=True)
        stats['total_projects'] = row['count'] if row else 0

        # Favorites
        sql = "SELECT COUNT(*) as count FROM projects WHERE enabled = 1 AND favorite = 1;"
        row = self._execute_query(sql, fetch_one=True)
        stats['favorites'] = row['count'] if row else 0

        # Most used tags
        sql = """
        SELECT tags FROM projects WHERE enabled = 1 AND tags IS NOT NULL;
        """
        rows = self._execute_query(sql, fetch_all=True)
        tag_counts = {}
        for row in rows:
            try:
                tags = json.loads(row['tags'])
                for tag in tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
            except (json.JSONDecodeError, TypeError):
                pass

        stats['tag_distribution'] = dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10])

        # Most opened
        sql = "SELECT name, open_count FROM projects WHERE enabled = 1 ORDER BY open_count DESC LIMIT 5;"
        rows = self._execute_query(sql, fetch_all=True)
        stats['most_opened'] = [{'name': row['name'], 'count': row['open_count']} for row in rows]

        return stats
