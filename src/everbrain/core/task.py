"""Task management: TaskManager service for workflow tasks.

Handles task creation, retrieval, and status updates with full type safety.
"""

import json
import uuid
from datetime import datetime
from typing import Any, Optional

from everbrain.storage.sqlite import DatabaseManager


class TaskManager:
    """Manages workflow tasks linked to sessions.
    
    Responsibilities:
    - Create new tasks
    - Query tasks by session
    - Update task status
    - Validate task ownership and existence
    """

    def __init__(self, db_manager: DatabaseManager) -> None:
        """Initialize TaskManager with database connection.
        
        Args:
            db_manager: Initialized DatabaseManager instance.
        """
        self.db = db_manager

    def create_task(
        self,
        session_id: str,
        title: str,
        description: Optional[str] = None,
        parent_id: Optional[str] = None,
    ) -> str:
        """Create a new task for the session.
        
        Args:
            session_id: Session ID to attach task to.
            title: Task title/summary (required).
            description: Optional detailed description.
            parent_id: Optional parent task ID for dependency graph.
            
        Returns:
            Created task ID (UUID).
            
        Raises:
            ValueError: If session doesn't exist or title is empty.
        """
        if not title.strip():
            raise ValueError("Task title cannot be empty")

        # Verify session exists
        session_check = self.db.execute_query(
            "SELECT id FROM sessions WHERE id = ?",
            (session_id,),
        )
        if not session_check:
            raise ValueError(f"Session {session_id} not found")

        task_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        query = """
        INSERT INTO tasks (id, session_id, title, description, status, parent_id, created_at, updated_at, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.db.execute_update(
            query,
            (task_id, session_id, title, description, "open", parent_id, now, now, json.dumps({})),
        )

        return task_id

    def list_open_tasks(self, session_id: str) -> list[dict[str, Any]]:
        """Get all open tasks for a session.
        
        Args:
            session_id: Session ID.
            
        Returns:
            List of task dicts with id, title, description, status, created_at.
            Ordered by creation date (newest first).
        """
        query = """
        SELECT id, title, description, status, created_at
        FROM tasks
        WHERE session_id = ? AND status = 'open'
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

    def get_task(self, task_id: str) -> Optional[dict[str, Any]]:
        """Get a single task by ID.
        
        Args:
            task_id: Task ID (full UUID or prefix).
            
        Returns:
            Task dict with id, session_id, title, description, status, created_at.
            Returns None if not found.
        """
        query = """
        SELECT id, session_id, title, description, status, created_at
        FROM tasks
        WHERE id = ? OR id LIKE ?
        """
        results = self.db.execute_query(query, (task_id, f"{task_id}%"))

        if results:
            row = results[0]
            return {
                "id": row["id"],
                "session_id": row["session_id"],
                "title": row["title"],
                "description": row["description"],
                "status": row["status"],
                "created_at": row["created_at"],
            }
        return None

    def complete_task(self, task_id: str, session_id: str) -> str:
        """Mark a task as completed.
        
        Args:
            task_id: Task ID to complete (full UUID or prefix).
            session_id: Session ID (for validation/ownership).
            
        Returns:
            The full task ID that was completed.
            
        Raises:
            ValueError: If task not found, doesn't belong to session, or already completed.
        """
        # Get task with prefix matching support
        query = """
        SELECT id, status FROM tasks
        WHERE (id = ? OR id LIKE ?) AND session_id = ?
        """
        results = self.db.execute_query(query, (task_id, f"{task_id}%", session_id))

        if not results:
            raise ValueError(
                f"Task '{task_id}' not found in current session"
            )

        if len(results) > 1:
            raise ValueError(
                f"Ambiguous task ID '{task_id}'. Matches multiple tasks. Use full ID."
            )

        row = results[0]
        full_task_id = row["id"]
        status = row["status"]

        if status == "completed":
            raise ValueError(f"Task '{task_id}' is already completed")

        now = datetime.utcnow().isoformat()
        update_query = """
        UPDATE tasks
        SET status = 'completed', updated_at = ?
        WHERE id = ?
        """
        self.db.execute_update(update_query, (now, full_task_id))
        return full_task_id
