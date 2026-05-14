"""CLI command: eb start - Start or resume an EverBrain session."""

from pathlib import Path

import typer
import yaml
from pydantic import ValidationError
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from everbrain.core.session import SessionManager
from everbrain.git.git_ops import get_git_status
from everbrain.models.config import EverBrainConfig
from everbrain.utils.console import (
    console,
    print_error,
    print_step,
)


def start_command() -> None:
    """Start or resume an EverBrain session for the current project.
    
    Creates a new session or resumes an existing one for the active Git branch.
    Displays a comprehensive startup dashboard with project info, branch status,
    active tasks, and next steps.
    
    Exits with code 1 if EverBrain is not initialized or on other errors.
    """
    # Step 1: Check if .everbrain directory exists
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
        # Step 2: Load config.yaml
        config_path = everbrain_dir / "config.yaml"
        if not config_path.exists():
            error_msg = "config.yaml not found. Try running [bold]eb init --force[/bold]."
            console.print(Panel(error_msg, style="bold red", title="Missing Config"))
            raise typer.Exit(code=1)

        print_step("Loading project configuration...")
        with open(config_path, "r", encoding="utf-8") as f:
            config_dict = yaml.safe_load(f)
        config = EverBrainConfig(**config_dict)

        # Step 3: Get current Git status
        print_step("Checking Git status...")
        git_status = get_git_status()
        branch = git_status["branch"]
        commit_hash = git_status["commit_hash"]
        commit_msg = git_status["commit_message"]

        # Step 4: Start or resume session
        print_step("Starting session...")
        session_manager = SessionManager.from_config_path(config_path)
        session_data = session_manager.start_or_resume_session(
            str(project_root), branch
        )

        # Step 5: Build and display the startup dashboard
        _display_startup_dashboard(
            config=config,
            session_data=session_data,
            git_status={
                "branch": branch,
                "commit_hash": commit_hash,
                "commit_msg": commit_msg,
            },
        )

    except yaml.YAMLError as e:
        print_error(f"Failed to parse config.yaml: {str(e)}")
        raise typer.Exit(code=1) from e
    except ValidationError as e:
        print_error(f"Invalid configuration: {str(e)}")
        raise typer.Exit(code=1) from e
    except typer.Exit:
        raise
    except Exception as e:
        print_error(f"Session start failed: {str(e)}")
        raise typer.Exit(code=1) from e


def _display_startup_dashboard(
    config: EverBrainConfig,
    session_data: dict,
    git_status: dict,
) -> None:
    """Display the beautiful startup dashboard.
    
    Args:
        config: Loaded EverBrainConfig.
        session_data: Session info from SessionManager.
        git_status: Git branch and commit info.
    """
    console.print()

    # ─────────────────────────────────────────────────────────────────────────
    # Project Information Panel
    # ─────────────────────────────────────────────────────────────────────────
    project_table = Table(show_header=False, box=None, padding=(0, 2))
    project_table.add_row("Project:", Text(config.project_name, style="bold cyan"))
    project_table.add_row("Root:", Text(str(config.project_root), style="dim"))

    console.print(
        Panel(
            project_table,
            title="[bold cyan]📁 Project[/bold cyan]",
            border_style="cyan",
            expand=False,
        )
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Git Status Panel
    # ─────────────────────────────────────────────────────────────────────────
    git_table = Table(show_header=False, box=None, padding=(0, 2))
    git_table.add_row("Branch:", Text(git_status["branch"], style="bold green"))
    git_table.add_row(
        "Latest Commit:",
        Text(f"{git_status['commit_hash']}", style="dim") + " "
        + Text(git_status["commit_msg"], style="italic"),
    )

    console.print(
        Panel(
            git_table,
            title="[bold green]🌳 Git[/bold green]",
            border_style="green",
            expand=False,
        )
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Session Status Panel
    # ─────────────────────────────────────────────────────────────────────────
    is_new = session_data["is_new"]
    session_status = (
        Text("🆕 New Session", style="bold yellow")
        if is_new
        else Text("↻ Resumed Session", style="bold blue")
    )

    session_table = Table(show_header=False, box=None, padding=(0, 2))
    session_table.add_row("Status:", session_status)
    session_table.add_row("Session ID:", Text(session_data["id"][:8], style="dim"))
    session_table.add_row(
        "Created:",
        Text(session_data["created_at"][:10], style="dim"),
    )

    console.print(
        Panel(
            session_table,
            title="[bold blue]📊 Session[/bold blue]",
            border_style="blue",
            expand=False,
        )
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Active Tasks Panel (if any)
    # ─────────────────────────────────────────────────────────────────────────
    active_tasks = session_data.get("active_tasks", [])
    if active_tasks:
        tasks_table = Table(
            title="Active Tasks",
            show_header=True,
            header_style="bold magenta",
            box=None,
        )
        tasks_table.add_column("Title", style="cyan")
        tasks_table.add_column("Status", style="yellow")

        for task in active_tasks[:5]:  # Show max 5 tasks
            tasks_table.add_row(
                task["title"][:40],
                Text(task["status"], style="bold yellow"),
            )

        if len(active_tasks) > 5:
            tasks_table.add_row(
                f"... +{len(active_tasks) - 5} more",
                "",
            )

        console.print(
            Panel(
                tasks_table,
                title="[bold magenta]✓ Active Tasks[/bold magenta]",
                border_style="magenta",
                expand=False,
            )
        )
    else:
        console.print(
            Panel(
                "No active tasks. Use [bold]eb task add[/bold] to create one.",
                title="[bold magenta]✓ Tasks[/bold magenta]",
                border_style="magenta",
                expand=False,
            )
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Next Steps
    # ─────────────────────────────────────────────────────────────────────────
    console.print()
    next_steps_text = (
        "[cyan]Next steps:[/cyan]\n"
        "  • Review active tasks above\n"
        "  • Use [bold]eb task add[/bold] to create a new task\n"
        "  • Use [bold]eb status[/bold] to check progress\n"
        "  • Use [bold]eb summary[/bold] to generate handoff notes (Phase 2+)"
    )
    console.print(Panel(next_steps_text, border_style="cyan", expand=False))

    console.print()
    console.print(
        Text("✅ Session started successfully!", style="bold green"),
    )
    console.print()
