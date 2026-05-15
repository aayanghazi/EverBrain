import sys
import typer

# On Windows, we need to force UTF-8 to avoid UnicodeEncodeError when printing emojis/tree characters.
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

from everbrain import __version__
from everbrain.cli.graph import graph_command
from everbrain.cli.init import init_command
from everbrain.cli.snapshot import snapshot_command
from everbrain.cli.start import start_command
from everbrain.cli.stop import stop_command
from everbrain.cli.summary import summary_command
from everbrain.cli.task import task_add_command, task_complete_command, task_list_command

# Create the main Typer app
app = typer.Typer(
    name="everbrain",
    help="Persistent workflow continuity for AI-assisted software development",
    no_args_is_help=True,
)

# Create task sub-command group
task_app = typer.Typer(help="Manage workflow tasks")


def version_callback(value: bool) -> None:
    """Display version information."""
    if value:
        typer.echo(f"everbrain {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """EverBrain: Persistent workflow continuity for AI-assisted development.
    
    Local-first CLI tool that preserves architecture understanding, coding standards,
    and active workflow state across sessions and AI agents.
    """
    pass


# Register top-level commands
app.command(name="init")(init_command)
app.command(name="start")(start_command)
app.command(name="stop")(stop_command)
app.command(name="summary")(summary_command)
app.command(name="graph")(graph_command)
app.command(name="snapshot")(snapshot_command)

# Register task sub-commands
task_app.command(name="add")(task_add_command)
task_app.command(name="list")(task_list_command)
task_app.command(name="complete")(task_complete_command)

# Add task sub-app to main app
app.add_typer(task_app, name="task")


if __name__ == "__main__":
    app()
