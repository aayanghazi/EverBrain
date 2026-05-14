"""Console utilities: Rich-based terminal output and formatting.

Provides a centralized console instance and helper functions for all CLI output.
Ensures consistent, beautiful error messages and user feedback.
"""

from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.style import Style

# Global console instance used by all CLI commands
console = Console()


def log_activity(message: str) -> None:
    """Append a timestamped message to the activity log.
    
    Creates .everbrain/logs/ directory if it doesn't exist.
    Logs are written to .everbrain/logs/activity.log in format:
    [YYYY-MM-DD HH:MM:SS] <message>
    
    Args:
        message: Message to log.
    """
    try:
        # Check if .everbrain exists relative to cwd
        everbrain_dir = Path.cwd() / ".everbrain"
        if not everbrain_dir.exists():
            return  # Silently skip if not in initialized project
        
        logs_dir = everbrain_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = logs_dir / "activity.log"
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception:
        # Silently fail - logging shouldn't break the application
        pass


def print_success(message: str) -> None:
    """Print a success message with green styling.
    
    Args:
        message: Message text to display.
    """
    console.print(f"✓ {message}", style=Style(color="green", bold=True))


def print_error(message: str) -> None:
    """Print an error message with red styling and panel.
    
    Args:
        message: Error message text to display.
    """
    log_activity(f"ERROR: {message}")
    console.print(Panel(message, style=Style(color="red", bold=True), title="Error"))


def print_step(message: str) -> None:
    """Print a step/progress message with blue styling.
    
    Args:
        message: Step message text to display.
    """
    log_activity(f"STEP: {message}")
    console.print(f"→ {message}", style=Style(color="blue"))


def print_info(message: str) -> None:
    """Print an informational message with cyan styling.
    
    Args:
        message: Info message text to display.
    """
    console.print(f"ℹ {message}", style=Style(color="cyan"))


def print_warning(message: str) -> None:
    """Print a warning message with yellow styling.
    
    Args:
        message: Warning message text to display.
    """
    console.print(f"⚠ {message}", style=Style(color="yellow", bold=True))
