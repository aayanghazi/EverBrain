"""Handoff engine: Session summary and report generation.

Generates markdown handoff reports for sessions, aggregating task state,
timeline, and recommendations for AI agents or developers resuming work.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from everbrain.core.task import TaskManager
from everbrain.storage.sqlite import DatabaseManager


class HandoffEngine:
    """Generates handoff reports for completed sessions."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        """Initialize HandoffEngine with database connection.
        
        Args:
            db_manager: Initialized DatabaseManager instance.
        """
        self.db = db_manager
        self.task_manager = TaskManager(db_manager)

    def generate_handoff(
        self,
        session_id: str,
        project_root: str,
        branch: str,
    ) -> str:
        """Generate a handoff report for a session.
        
        Aggregates session metadata, tasks, and recommendations into a markdown report.
        
        Args:
            session_id: Session ID.
            project_root: Project root directory.
            branch: Git branch name.
            
        Returns:
            Markdown content as string.
            
        Raises:
            ValueError: If session not found.
        """
        # Fetch session metadata
        session_query = "SELECT id, created_at, last_active, metadata FROM sessions WHERE id = ?"
        results = self.db.execute_query(session_query, (session_id,))

        if not results:
            raise ValueError(f"Session {session_id} not found")

        session_row = results[0]
        metadata = json.loads(session_row["metadata"]) if session_row["metadata"] else {}

        # Fetch all tasks (completed and open)
        tasks_query = """
        SELECT id, title, status, created_at, updated_at
        FROM tasks
        WHERE session_id = ?
        ORDER BY status DESC, updated_at DESC
        """
        tasks_results = self.db.execute_query(tasks_query, (session_id,))

        completed_tasks = []
        open_tasks = []

        for task_row in tasks_results:
            task = {
                "id": task_row["id"],
                "title": task_row["title"],
                "created_at": task_row["created_at"],
                "updated_at": task_row["updated_at"],
            }
            if task_row["status"] == "completed":
                completed_tasks.append(task)
            else:
                open_tasks.append(task)

        # Generate markdown report
        report = self._build_markdown_report(
            session_id=session_id,
            branch=branch,
            project_root=project_root,
            created_at=session_row["created_at"],
            stopped_at=datetime.utcnow().isoformat(),
            metadata=metadata,
            completed_tasks=completed_tasks,
            open_tasks=open_tasks,
        )

        return report

    def save_handoff(self, handoff_dir: Path, session_id: str, content: str) -> Path:
        """Save handoff report to markdown file.
        
        Args:
            handoff_dir: Directory to save handoff files.
            session_id: Session ID (used in filename).
            content: Markdown content.
            
        Returns:
            Path to saved file.
        """
        handoff_file = handoff_dir / f"session_{session_id[:8]}.md"
        with open(handoff_file, "w", encoding="utf-8") as f:
            f.write(content)
        return handoff_file

    def _build_markdown_report(
        self,
        session_id: str,
        branch: str,
        project_root: str,
        created_at: str,
        stopped_at: str,
        metadata: dict[str, Any],
        completed_tasks: list[dict[str, Any]],
        open_tasks: list[dict[str, Any]],
    ) -> str:
        """Build markdown handoff report.
        
        Args:
            session_id: Session ID.
            branch: Git branch.
            project_root: Project root.
            created_at: Session creation timestamp.
            stopped_at: Session stop timestamp.
            metadata: Session metadata dict.
            completed_tasks: List of completed task dicts.
            open_tasks: List of open task dicts.
            
        Returns:
            Markdown content.
        """
        lines = [
            "# EverBrain Handoff Report",
            "",
            f"**Session ID:** `{session_id[:8]}`",
            f"**Branch:** `{branch}`",
            f"**Project:** {project_root}",
            "",
            "## Timeline",
            "",
            f"- **Started:** {created_at[:19]}",
            f"- **Stopped:** {stopped_at[:19]}",
            "",
        ]

        # Session metadata section
        if metadata:
            lines.extend(
                [
                    "## Session Context",
                    "",
                ]
            )
            for key, value in metadata.items():
                lines.append(f"- **{key.replace('_', ' ').title()}:** {value}")
            lines.append("")

        # Completed tasks section
        if completed_tasks:
            lines.extend(
                [
                    f"## ✅ Completed Tasks ({len(completed_tasks)})",
                    "",
                ]
            )
            for task in completed_tasks:
                lines.append(
                    f"- [x] **{task['title']}**"
                )
                lines.append(f"  - Completed: {task['updated_at'][:19]}")
            lines.append("")

        # Open tasks section
        if open_tasks:
            lines.extend(
                [
                    f"## 📋 Open Tasks ({len(open_tasks)})",
                    "",
                    "*These tasks were not completed during this session.*",
                    "",
                ]
            )
            for task in open_tasks:
                lines.append(f"- [ ] **{task['title']}**")
                lines.append(f"  - Created: {task['created_at'][:19]}")
            lines.append("")

        # Recommendations section
        lines.extend(
            [
                "## 🎯 Recommendations for Next Session",
                "",
                "1. Review open tasks listed above",
                "2. Consider the context and timeline of work",
                "3. Start with highest-priority incomplete tasks",
                "4. Run `eb start` to resume or begin a new session",
                "",
            ]
        )

        # Footer
        lines.extend(
            [
                "---",
                "",
                "*Generated by EverBrain — Persistent Workflow Continuity*",
                f"*Report generated: {datetime.utcnow().isoformat()[:19]}*",
            ]
        )

        return "\n".join(lines)
