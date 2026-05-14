"""Core session management: SessionManager for workflow continuity.

Handles session lifecycle: creation, resumption, task tracking.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from everbrain.models.config import EverBrainConfig
from everbrain.storage.sqlite import DatabaseManager


class SessionManager:
    """Manages development sessions and task persistence.
    
    Responsibilities:
    - Create or resume sessions per Git branch
    - Track active tasks within a session
    - Persist session metadata (branch, project state, etc.)
    - Query historical session data
    """

    def __init__(self, db_manager: DatabaseManager) -> None:
        """Initialize SessionManager with a database connection.
        
        Args:
            db_manager: Initialized DatabaseManager instance.
        """
        self.db = db_manager

    def start_or_resume_session(
        self,
        project_root: str,
        branch_name: str,
    ) -> dict[str, Any]:
        """Start a new session or resume an existing one for the given branch.
        
        **Logic:**
        1. Query for an existing session with matching project_root and branch
        2. If found AND not stopped:
           - Mark as resumed and update last_active timestamp
           - Fetch active tasks
        3. If found AND is stopped:
           - Create a new session (prevents zombie sessions)
        4. If not found:
           - Create new session
        
        Args:
            project_root: Absolute path to project directory.
            branch_name: Current Git branch name.
            
        Returns:
            Dict with session data:
            {
                'id': session_id,
                'project_root': project_root,
                'branch': branch_name,
                'is_new': bool,
                'created_at': timestamp,
                'active_tasks': [task_dicts],
            }
        """
        # Step 1: Try to find existing session for this branch
        existing_session = self._find_session_by_branch(project_root, branch_name)

        if existing_session:
            # Check if session is stopped
            metadata = existing_session.get("metadata", {})
            is_stopped = "stopped_at" in metadata

            if is_stopped:
                # Step 3: Create new session (prevent zombie sessions)
                session_id = str(uuid.uuid4())
                is_new = True
                self._create_session(session_id, project_root, branch_name)
            else:
                # Step 2: Resume existing active session
                session_id = existing_session["id"]
                is_new = False
                self._update_session_activity(session_id)
        else:
            # Step 4: Create new session
            session_id = str(uuid.uuid4())
            is_new = True
            self._create_session(session_id, project_root, branch_name)

        # Fetch active tasks for this session
        active_tasks = self._get_active_tasks(session_id)

        return {
            "id": session_id,
            "project_root": project_root,
            "branch": branch_name,
            "is_new": is_new,
            "created_at": existing_session["created_at"]
            if existing_session and not (
                "stopped_at" in existing_session.get("metadata", {})
            )
            else datetime.utcnow().isoformat(),
            "active_tasks": active_tasks,
        }

    def _find_session_by_branch(
        self, project_root: str, branch_name: str
    ) -> Optional[dict[str, Any]]:
        """Find an existing session by project root and branch.
        
        Queries all sessions for the project and checks metadata for branch match.
        
        Args:
            project_root: Project directory path.
            branch_name: Git branch name.
            
        Returns:
            Session dict or None if not found.
        """
        query = """
        SELECT id, project_root, created_at, metadata
        FROM sessions
        WHERE project_root = ?
        """
        results = self.db.execute_query(query, (project_root,))

        for row in results:
            metadata = json.loads(row["metadata"]) if row["metadata"] else {}
            stored_branch = metadata.get("branch", "main")

            # Match by branch name
            if stored_branch == branch_name:
                return {
                    "id": row["id"],
                    "project_root": row["project_root"],
                    "created_at": row["created_at"],
                    "metadata": metadata,
                }

        return None

    def _create_session(
        self, session_id: str, project_root: str, branch_name: str
    ) -> None:
        """Create a new session in the database.
        
        Args:
            session_id: Unique session identifier.
            project_root: Project directory path.
            branch_name: Current Git branch.
        """
        metadata: dict[str, Any] = {
            "branch": branch_name,
            "created_by": "eb start",
        }
        now = datetime.utcnow().isoformat()

        query = """
        INSERT INTO sessions (id, project_root, created_at, last_active, metadata)
        VALUES (?, ?, ?, ?, ?)
        """
        self.db.execute_update(
            query,
            (session_id, project_root, now, now, json.dumps(metadata)),
        )

    def _update_session_activity(self, session_id: str) -> None:
        """Update the last_active timestamp for a session.
        
        Args:
            session_id: Session to update.
        """
        now = datetime.utcnow().isoformat()
        query = "UPDATE sessions SET last_active = ? WHERE id = ?"
        self.db.execute_update(query, (now, session_id))

    def _get_active_tasks(self, session_id: str) -> list[dict[str, Any]]:
        """Get all active tasks for a session.
        
        Args:
            session_id: Session ID.
            
        Returns:
            List of task dicts with status != 'completed'.
        """
        query = """
        SELECT id, title, description, status, created_at
        FROM tasks
        WHERE session_id = ? AND status != 'completed'
        ORDER BY created_at DESC
        """
        results = self.db.execute_query(query, (session_id,))

        tasks = []
        for row in results:
            tasks.append(
                {
                    "id": row["id"],
                    "title": row["title"],
                    "description": row["description"],
                    "status": row["status"],
                    "created_at": row["created_at"],
                }
            )
        return tasks

    @staticmethod
    def from_config_path(config_path: Path) -> "SessionManager":
        """Create a SessionManager from a config file path.
        
        Args:
            config_path: Path to config.yaml.
            
        Returns:
            Initialized SessionManager.
        """
        # Load config
        import yaml

        with open(config_path, "r", encoding="utf-8") as f:
            config_dict = yaml.safe_load(f)

        config = EverBrainConfig(**config_dict)

        # Resolve database path
        project_root = config.project_root
        db_path_str = config.get_memory_db_path(project_root)
        db_path = Path(db_path_str)

        # Initialize database manager
        db_manager = DatabaseManager(db_path)
        db_manager.connect()

        return SessionManager(db_manager)
