"""CLI command: eb snapshot - Create a project snapshot."""

import shutil
from datetime import datetime
from pathlib import Path

import typer

from everbrain.utils.console import console, print_error, print_step, print_success


def snapshot_command(
    label: str = typer.Argument(..., help="Snapshot label/identifier"),
) -> None:
    """Create a snapshot of the project state.
    
    Creates a timestamped directory in .everbrain/snapshots/ containing:
    - memory.db (task database)
    - config.yaml (project configuration)
    - rules.yaml (project rules)
    
    Snapshots are useful for archiving project state at milestones.
    
    Args:
        label: Custom label for the snapshot (e.g., "feature-complete", "release-v1").
    """
    try:
        project_root = Path.cwd()
        everbrain_dir = project_root / ".everbrain"

        if not everbrain_dir.exists():
            error_msg = (
                "EverBrain is not initialized in this project.\n"
                "Run [bold]eb init[/bold] to set up EverBrain."
            )
            console.print(error_msg, style="bold red")
            raise typer.Exit(code=1)

        # Validate required files exist
        required_files = {
            "memory.db": everbrain_dir / "memory.db",
            "config.yaml": everbrain_dir / "config.yaml",
            "rules.yaml": everbrain_dir / "rules.yaml",
        }

        for name, file_path in required_files.items():
            if not file_path.exists():
                print_error(f"Required file not found: {name}")
                raise typer.Exit(code=1)

        # Create snapshots directory
        snapshots_dir = everbrain_dir / "snapshots"
        snapshots_dir.mkdir(parents=True, exist_ok=True)

        # Create timestamped snapshot directory
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        snapshot_name = f"snapshot_{timestamp}_{label}"
        snapshot_dir = snapshots_dir / snapshot_name

        if snapshot_dir.exists():
            print_error(f"Snapshot directory already exists: {snapshot_dir.name}")
            raise typer.Exit(code=1)

        snapshot_dir.mkdir(parents=True, exist_ok=True)

        print_step(f"Creating snapshot: {snapshot_name}...")

        # Copy files using shutil
        try:
            shutil.copy2(
                required_files["memory.db"],
                snapshot_dir / "memory.db",
            )
            shutil.copy2(
                required_files["config.yaml"],
                snapshot_dir / "config.yaml",
            )
            shutil.copy2(
                required_files["rules.yaml"],
                snapshot_dir / "rules.yaml",
            )
        except IOError as e:
            print_error(f"Failed to copy snapshot files: {str(e)}")
            # Cleanup on failure
            shutil.rmtree(snapshot_dir, ignore_errors=True)
            raise typer.Exit(code=1) from e

        console.print()
        print_success("Snapshot created successfully!")
        console.print()
        console.print(
            f"Location: [cyan]{snapshot_dir.relative_to(project_root)}[/cyan]"
        )
        console.print(f"Files backed up:")
        console.print(f"  • memory.db")
        console.print(f"  • config.yaml")
        console.print(f"  • rules.yaml")
        console.print()

    except typer.Exit:
        raise
    except Exception as e:
        print_error(f"Failed to create snapshot: {str(e)}")
        raise typer.Exit(code=1) from e
