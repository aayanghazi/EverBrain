"""CLI command: eb graph - Visualize task dependency hierarchy."""

from datetime import datetime
from pathlib import Path

import typer
import yaml
from pydantic import ValidationError
from rich.console import Console
from rich.panel import Panel

from everbrain.core.graph import build_task_tree
from everbrain.models.config import EverBrainConfig
from everbrain.storage.sqlite import DatabaseManager
from everbrain.utils.console import (
    console,
    print_error,
    print_step,
)

app = typer.Typer(help="Visualize the task dependency graph")


def graph_command(
    export: bool = typer.Option(
        False,
        "--export",
        help="Save graph to file",
    ),
) -> None:
    """Display the task dependency graph as a tree.

    Fetches all tasks from the database, builds a hierarchical
    tree based on parent_id relationships, and prints it.
    
    With --export, saves the visualization to .everbrain/graph/graph_YYYYMMDD_HHMMSS.txt
    """
    try:
        project_root = Path.cwd()
        everbrain_dir = project_root / ".everbrain"

        if not everbrain_dir.exists():
            console.print(
                Panel(
                    "EverBrain is not initialized in this project.\n"
                    "Run [bold]eb init[/bold] to set up EverBrain.",
                    style="bold red",
                    title="Not Initialized",
                )
            )
            raise typer.Exit(code=1)

        config_path = everbrain_dir / "config.yaml"
        if not config_path.exists():
            console.print(
                Panel(
                    "config.yaml not found. Try running [bold]eb init --force[/bold].",
                    style="bold red",
                    title="Missing Config",
                )
            )
            raise typer.Exit(code=1)

        with open(config_path, "r", encoding="utf-8") as f:
            config_dict = yaml.safe_load(f)
        config = EverBrainConfig(**config_dict)

        db_path = everbrain_dir / "memory.db"
        db_manager = DatabaseManager(db_path)

        print_step("Building task graph...")

        tasks = db_manager.get_all_tasks()
        tree = build_task_tree(tasks)

        console.print()
        console.print(tree)
        console.print()

        # Export to file if requested
        if export:
            graph_dir = everbrain_dir / "graph"
            graph_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            graph_file = graph_dir / f"graph_{timestamp}.txt"
            
            # Create a separate console for file output
            file_console = Console(file=open(graph_file, "w", encoding="utf-8"))
            file_console.print(tree)
            file_console.file.close()
            
            print_step(f"Graph exported: {graph_file.relative_to(project_root)}")

        db_manager.close()

    except ValidationError as e:
        print_error(f"Invalid configuration: {str(e)}")
        raise typer.Exit(code=1) from e
    except typer.Exit:
        raise
    except Exception as e:
        print_error(f"Failed to build graph: {str(e)}")
        raise typer.Exit(code=1) from e
