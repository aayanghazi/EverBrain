"""CLI commands: eb task - Task management suite."""

from pathlib import Path

import typer
import yaml
from pydantic import ValidationError
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from everbrain.core.session import SessionManager
from everbrain.core.task import TaskManager
from everbrain.git.git_ops import get_git_status
from everbrain.models.config import EverBrainConfig
from everbrain.utils.console import (
    console,
    print_error,
    print_step,
    print_success,
)


def _get_current_session_and_db() -> tuple[Path, SessionManager, dict[str, str]]:
    """Helper: Get current session and database connection.
    
    Returns:
        Tuple of (everbrain_dir, session_manager, session_data).
        
    Raises:
        typer.Exit: If EverBrain not initialized or session retrieval fails.
    """
    project_root = Path.cwd()
    everbrain_dir = project_root / ".everbrain"

    if not everbrain_dir.exists():
        error_msg = (
            "EverBrain is not initialized in this project.\n"
            "Run [bold]eb init[/bold] to set up EverBrain."
        )
        console.print(Panel(error_msg, style="bold red", title="Not Initialized"))
        raise typer.Exit(code=1)

    try:
        config_path = everbrain_dir / "config.yaml"
        if not config_path.exists():
            error_msg = "config.yaml not found. Try running [bold]eb init --force[/bold]."
            console.print(Panel(error_msg, style="bold red", title="Missing Config"))
            raise typer.Exit(code=1)

        with open(config_path, "r", encoding="utf-8") as f:
            config_dict = yaml.safe_load(f)
        config = EverBrainConfig(**config_dict)

        # Get current session
        session_manager = SessionManager.from_config_path(config_path)
        git_status = get_git_status()
        branch = git_status["branch"]

        session_data = session_manager.start_or_resume_session(
            str(project_root), branch
        )

        return everbrain_dir, session_manager, session_data

    except ValidationError as e:
        print_error(f"Invalid configuration: {str(e)}")
        raise typer.Exit(code=1) from e
    except typer.Exit:
        raise
    except Exception as e:
        print_error(f"Failed to load session: {str(e)}")
        raise typer.Exit(code=1) from e


def task_add_command(
    title: str = typer.Argument(..., help="Task title/description"),
    parent: str = typer.Option(
        None,
        "--parent",
        "-p",
        help="Parent task ID to link this task as a sub-task",
    ),
) -> None:
    """Create a new task for the current session.
    
    Example:
        eb task add "Implement authentication"
        eb task add "Write login form" --parent abc123de
    """
    try:
        print_step("Creating task...")

        everbrain_dir, session_manager, session_data = _get_current_session_and_db()
        session_id = session_data["id"]

        # Create task
        task_manager = TaskManager(session_manager.db)
        task_id = task_manager.create_task(
            session_id=session_id, title=title, parent_id=parent
        )

        console.print()

        parent_info = ""
        if parent:
            parent_info = f"\nParent: [dim]{parent[:8]}[/dim]"

        console.print(
            Panel(
                f"[bold green]✓ Task created![/bold green]\n\n"
                f"ID:    [cyan]{task_id[:8]}[/cyan]\n"
                f"Title: [yellow]{title}[/yellow]{parent_info}",
                border_style="green",
                expand=False,
            )
        )
        console.print()

    except ValueError as e:
        print_error(f"Invalid task: {str(e)}")
        raise typer.Exit(code=1) from e
    except Exception as e:
        print_error(f"Failed to create task: {str(e)}")
        raise typer.Exit(code=1) from e


def task_list_command() -> None:
    """List all open tasks for the current session."""
    try:
        print_step("Fetching tasks...")

        everbrain_dir, session_manager, session_data = _get_current_session_and_db()
        session_id = session_data["id"]

        # Get tasks
        task_manager = TaskManager(session_manager.db)
        tasks = task_manager.list_open_tasks(session_id)

        console.print()

        if not tasks:
            console.print(
                Panel(
                    "No active tasks for this session.\n"
                    "Use [bold]eb task add[/bold] to create one.",
                    border_style="cyan",
                    expand=False,
                )
            )
        else:
            # Build table
            table = Table(
                title=f"📋 Active Tasks ({len(tasks)} task{'s' if len(tasks) != 1 else ''})",
                show_header=True,
                header_style="bold magenta",
                expand=True,
            )
            table.add_column("ID", style="cyan", width=10)
            table.add_column("Title", style="white")
            table.add_column("Created", style="dim", width=12)

            for task in tasks:
                task_id_short = task["id"][:8]
                created_date = task["created_at"][:10]
                table.add_row(task_id_short, task["title"], created_date)

            console.print(table)

        console.print()

    except Exception as e:
        print_error(f"Failed to list tasks: {str(e)}")
        raise typer.Exit(code=1) from e


def task_complete_command(
    task_id: str = typer.Argument(..., help="Task ID or ID prefix to complete")
) -> None:
    """Mark a task as completed.
    
    Example:
        eb task complete abc123de
    """
    try:
        print_step(f"Completing task: {task_id}...")

        everbrain_dir, session_manager, session_data = _get_current_session_and_db()
        session_id = session_data["id"]

        # Complete task
        task_manager = TaskManager(session_manager.db)
        completed_id = task_manager.complete_task(task_id, session_id)

        # Get task for display
        task = task_manager.get_task(completed_id)

        console.print()
        console.print(
            Panel(
                f"[bold green]✓ Task completed![/bold green]\n\n"
                f"ID:    [cyan]{completed_id[:8]}[/cyan]\n"
                f"Title: [yellow]{task['title']}[/yellow]",
                border_style="green",
                expand=False,
            )
        )
        console.print()

    except ValueError as e:
        print_error(f"Task error: {str(e)}")
        raise typer.Exit(code=1) from e
    except Exception as e:
        print_error(f"Failed to complete task: {str(e)}")
        raise typer.Exit(code=1) from e
