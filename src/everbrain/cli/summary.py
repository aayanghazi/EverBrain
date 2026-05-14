"""CLI command: eb summary - View session handoff reports."""

from datetime import datetime
from pathlib import Path

import typer
from rich.markdown import Markdown
from rich.panel import Panel

from everbrain.utils.console import console, print_error, print_step


def summary_command(
    session_id: str = typer.Option(
        None,
        "--session",
        "-s",
        help="Session ID or prefix (default: latest)",
    ),
) -> None:
    """View handoff reports for completed sessions.
    
    Displays the markdown report for a session. If no session specified,
    shows the most recent report.
    
    Also saves a timestamped copy to .everbrain/summaries/summary_YYYYMMDD_HHMMSS.md
    """
    try:
        project_root = Path.cwd()
        everbrain_dir = project_root / ".everbrain"
        handoff_dir = everbrain_dir / "handoffs"

        if not handoff_dir.exists():
            console.print(
                Panel(
                    "No handoff reports found yet.\n"
                    "Run [bold]eb stop[/bold] to generate one.",
                    border_style="cyan",
                    expand=False,
                )
            )
            return

        # Find report files
        report_files = list(handoff_dir.glob("session_*.md"))

        if not report_files:
            console.print(
                Panel(
                    "No handoff reports found yet.\n"
                    "Run [bold]eb stop[/bold] to generate one.",
                    border_style="cyan",
                    expand=False,
                )
            )
            return

        # Select report
        if session_id:
            # Find matching report
            matching = [f for f in report_files if session_id in f.name]
            if not matching:
                print_error(f"No report found for session '{session_id}'")
                raise typer.Exit(code=1)
            report_file = matching[0]
        else:
            # Get most recent
            report_file = sorted(report_files, key=lambda f: f.stat().st_mtime)[-1]

        print_step(f"Loading report: {report_file.name}...")

        # Read report content
        with open(report_file, "r", encoding="utf-8") as f:
            content = f.read()

        console.print()
        console.print(
            Panel(
                Markdown(content),
                border_style="cyan",
                title="[bold cyan]📋 Handoff Report[/bold cyan]",
                expand=True,
            )
        )
        console.print()

        # Save timestamped copy to summaries directory
        summaries_dir = everbrain_dir / "summaries"
        summaries_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        summary_file = summaries_dir / f"summary_{timestamp}.md"
        
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write(content)
        
        print_step(f"Summary saved: {summary_file.relative_to(project_root)}")

    except Exception as e:
        print_error(f"Failed to load summary: {str(e)}")
        raise typer.Exit(code=1) from e
