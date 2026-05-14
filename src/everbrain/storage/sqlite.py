"""SQLite database management and connection handling.

Provides a clean database abstraction layer with proper initialization,
schema management, and repository pattern support.
"""

import sqlite3
from pathlib import Path
from typing import Optional


class DatabaseManager:
    """Manages SQLite database connections and schema initialization.
    
    Handles:
    - Database connection lifecycle
    - Table schema creation
    - Transaction management
    - Graceful cleanup
    
    No direct SQL queries should be executed outside repository classes.
    """

    def __init__(self, db_path: Path) -> None:
        """Initialize DatabaseManager with database file path.
        
        Args:
            db_path: Absolute path to the SQLite database file.
                    File is created if it does not exist.
        """
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        """Establish or retrieve database connection.
        
        Returns:
            sqlite3.Connection: Active database connection.
            
        Raises:
            sqlite3.Error: If connection fails.
        """
        if self._connection is None:
            try:
                self.db_path.parent.mkdir(parents=True, exist_ok=True)
                self._connection = sqlite3.connect(
                    str(self.db_path),
                    timeout=10.0,
                    check_same_thread=False,
                )
                self._connection.row_factory = sqlite3.Row
                # Enable foreign keys
                self._connection.execute("PRAGMA foreign_keys = ON")
            except sqlite3.Error as e:
                raise sqlite3.Error(f"Failed to connect to database: {e}") from e
        return self._connection

    def close(self) -> None:
        """Close database connection."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def initialize_schema(self) -> None:
        """Create all required database tables.
        
        Called once during `eb init` to bootstrap the database.
        Idempotent: safe to call multiple times.
        
        Raises:
            sqlite3.Error: If schema creation fails.
        """
        conn = self.connect()
        cursor = conn.cursor()

        try:
            # Sessions table: tracks development sessions (multiple per project, one per branch)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    project_root TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
                """
            )

            # Tasks table: tracks workflow tasks and blockers
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL DEFAULT 'active',
                    parent_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                )
                """
            )

            # Create indexes for common queries
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_sessions_project ON sessions(project_root)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_tasks_session ON tasks(session_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_sessions_active ON sessions(last_active)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_tasks_parent ON tasks(parent_id)"
            )

            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            raise sqlite3.Error(f"Failed to initialize database schema: {e}") from e
        finally:
            cursor.close()

    def execute_query(
        self, query: str, params: tuple[object, ...] = ()
    ) -> list[sqlite3.Row]:
        """Execute a SELECT query and return results.
        
        Args:
            query: SQL SELECT query string.
            params: Query parameters for parameterized queries.
            
        Returns:
            List of rows as sqlite3.Row objects.
            
        Raises:
            sqlite3.Error: If query execution fails.
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            cursor.close()
            return results
        except sqlite3.Error as e:
            raise sqlite3.Error(f"Query execution failed: {e}") from e

    def execute_update(
        self, query: str, params: tuple[object, ...] = ()
    ) -> int:
        """Execute an INSERT, UPDATE, or DELETE query.
        
        Args:
            query: SQL modification query string.
            params: Query parameters for parameterized queries.
            
        Returns:
            Number of rows affected.
            
        Raises:
            sqlite3.Error: If query execution fails.
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows_affected = cursor.rowcount
            conn.commit()
            cursor.close()
            return rows_affected
        except sqlite3.Error as e:
            conn.rollback()
            raise sqlite3.Error(f"Update execution failed: {e}") from e

    def __enter__(self) -> "DatabaseManager":
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        """Context manager exit: close connection on exit."""
        self.close()

    def get_all_tasks(self) -> list[dict[str, object]]:
        """Retrieve all tasks with parent_id for graph construction.

        Returns:
            List of task dicts with id, title, status, and parent_id.
        """
        query = """
        SELECT id, session_id, title, description, status, parent_id, created_at
        FROM tasks
        ORDER BY created_at ASC
        """
        results = self.execute_query(query)
        return [
            {
                "id": row["id"],
                "session_id": row["session_id"],
                "title": row["title"],
                "description": row["description"],
                "status": row["status"],
                "parent_id": row["parent_id"],
                "created_at": row["created_at"],
            }
            for row in results
        ]

    def __repr__(self) -> str:
        """Return string representation of DatabaseManager."""
        return f"DatabaseManager(db_path={self.db_path}, connected={self._connection is not None})"
