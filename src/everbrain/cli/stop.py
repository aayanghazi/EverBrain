"""CLI command: eb stop - Stop the current session and generate handoff."""

from pathlib import Path

import typer
import yaml
from pydantic import ValidationError
from rich.markdown import Markdown
from rich.panel import Panel

from everbrain.core.handoff import HandoffEngine
from everbrain.core.session import SessionManager
from everbrain.git.git_ops import get_git_status
from everbrain.models.config import EverBrainConfig
from everbrain.utils.console import (
    console,
    print_error,
    print_step,
    print_success,
)


def stop_command() -> None:
    """Stop the current session and generate a handoff report.
    
    The handoff report summarizes:
    - Completed tasks
    - Open tasks
    - Session timeline
    - Recommendations for next session
    
    Report is saved to .everbrain/handoffs/ for future reference.
    """
    try:
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

            print_step("Loading project configuration...")
            with open(config_path, "r", encoding="utf-8") as f:
                config_dict = yaml.safe_load(f)
            config = EverBrainConfig(**config_dict)

            # Get current session
            print_step("Retrieving current session...")
            session_manager = SessionManager.from_config_path(config_path)
            git_status = get_git_status()
            branch = git_status["branch"]

            session_data = session_manager.start_or_resume_session(
                str(project_root), branch
            )
            session_id = session_data["id"]

            # Mark session as stopped
            print_step("Generating handoff report...")
            now_iso = __import__("datetime").datetime.utcnow().isoformat()
            session_manager.db.execute_update(
                "UPDATE sessions SET metadata = ? WHERE id = ?",
                (
                    __import__("json").dumps({"branch": branch, "stopped_at": now_iso}),
                    session_id,
                ),
            )

            # Generate handoff
            handoff_engine = HandoffEngine(session_manager.db)
            handoff_content = handoff_engine.generate_handoff(
                session_id=session_id,
                project_root=str(project_root),
                branch=branch,
            )

            # Save handoff file
            handoff_dir = everbrain_dir / "handoffs"
            handoff_dir.mkdir(parents=True, exist_ok=True)
            handoff_file = handoff_engine.save_handoff(
                handoff_dir, session_id, handoff_content
            )

            # Display report
            console.print()
            console.print(
                Panel(
                    Markdown(handoff_content),
                    border_style="cyan",
                    title="[bold cyan]📋 Handoff Report[/bold cyan]",
                    expand=True,
                )
            )
            console.print()

            # Success message
            console.print(
                Panel(
                    f"[bold green]✓ Session stopped successfully![/bold green]\n\n"
                    f"Report saved: [cyan]{handoff_file.relative_to(project_root)}[/cyan]\n"
                    f"Session ID: [cyan]{session_id[:8]}[/cyan]\n\n"
                    f"Next: Run [bold]eb start[/bold] to begin a new session.",
                    border_style="green",
                    expand=False,
                )
            )
            console.print()

        except ValidationError as e:
            print_error(f"Invalid configuration: {str(e)}")
            raise typer.Exit(code=1) from e
        except typer.Exit:
            raise
        except Exception as e:
            print_error(f"Failed to stop session: {str(e)}")
            raise typer.Exit(code=1) from e

    except Exception as e:
        print_error(f"Session stop failed: {str(e)}")
        raise typer.Exit(code=1) from e
