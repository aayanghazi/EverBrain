"""Data models: Pydantic configuration and domain schemas.

Provides strict type-safe validation for:
- CLI configuration (config.yaml)
- Application rules (rules.yaml)
- Domain objects (sessions, tasks, etc.)
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class TaskModel(BaseModel):
    """Represents a single development task or workflow item."""

    id: str = Field(..., description="Unique task identifier (UUID)")
    session_id: str = Field(..., description="Associated session ID")
    title: str = Field(..., min_length=1, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    status: str = Field(
        default="active",
        description="Task status: active, blocked, completed, deferred",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Task creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )
    parent_id: Optional[str] = Field(None, description="Parent task ID for dependency graph")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Custom metadata")

    model_config = {"json_schema_extra": {"example": "See TaskModel usage"}}


class SessionModel(BaseModel):
    """Represents a development session (e.g., one 'eb start' invocation)."""

    id: str = Field(..., description="Unique session identifier (UUID)")
    project_root: str = Field(..., description="Absolute path to project root")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Session start timestamp"
    )
    last_active: datetime = Field(
        default_factory=datetime.utcnow, description="Last activity timestamp"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Custom metadata")

    model_config = {"json_schema_extra": {"example": "See SessionModel usage"}}


class EverBrainConfig(BaseModel):
    """Top-level EverBrain configuration (from config.yaml).
    
    Provides centralized configuration with strict validation.
    Extensible for future settings (project name, author, etc.).
    """

    # Workspace identification
    project_name: str = Field(..., description="Name of the project")
    project_root: str = Field(..., description="Absolute path to project root")

    # Version and compatibility
    version: str = Field(default="0.1.0", description="Config schema version")
    everbrain_version: str = Field(default="0.1.0", description="EverBrain version")

    # Storage settings
    memory_db_path: Optional[str] = Field(
        default=".everbrain/memory.db",
        description="Relative path to SQLite database from project root",
    )

    # Logging and debug settings
    log_level: str = Field(
        default="INFO",
        description="Logging level: DEBUG, INFO, WARNING, ERROR",
    )
    debug_mode: bool = Field(default=False, description="Enable debug mode")

    # Extension points (Phase 2+)
    extensions: dict[str, Any] = Field(default_factory=dict, description="Plugin config")

    model_config = {
        "json_schema_extra": {
            "example": {
                "project_name": "my-project",
                "project_root": "/path/to/project",
                "version": "0.1.0",
                "everbrain_version": "0.1.0",
                "memory_db_path": ".everbrain/memory.db",
                "log_level": "INFO",
                "debug_mode": False,
                "extensions": {},
            }
        }
    }

    def get_memory_db_path(self, base_path: str) -> str:
        """Resolve absolute path to memory database.
        
        Args:
            base_path: Base directory for relative path resolution.
            
        Returns:
            Absolute path to memory database file.
        """
        if self.memory_db_path is None:
            return ""
        # Handle both relative and absolute paths
        if self.memory_db_path.startswith("/") or ":" in self.memory_db_path:
            return self.memory_db_path
        # Relative path: resolve from project root
        return f"{base_path}/{self.memory_db_path}"


class RulesConfig(BaseModel):
    """Project-level coding rules and standards (from rules.yaml).
    
    Future-proofed for Phase 2+ (AST validation, linting rules, etc.).
    Currently stores metadata for handoff and context continuity.
    """

    # Architecture standards
    architecture_notes: Optional[str] = Field(
        default=None, description="High-level architecture documentation"
    )

    # Code style enforcement (Phase 2+: connected to linters)
    style_guide: dict[str, Any] = Field(
        default_factory=dict, description="Code style rules and standards"
    )

    # Forbidden patterns and gotchas
    forbidden_patterns: list[str] = Field(
        default_factory=list, description="Regex patterns to avoid"
    )

    # Custom metadata
    metadata: dict[str, Any] = Field(default_factory=dict, description="Custom rules")

    model_config = {
        "json_schema_extra": {
            "example": {
                "architecture_notes": "Monorepo with packages/",
                "style_guide": {"line_length": 100, "python_version": "3.12"},
                "forbidden_patterns": [],
                "metadata": {},
            }
        }
    }
