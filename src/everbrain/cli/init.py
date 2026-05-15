"""CLI command: eb init - Initialize EverBrain in a project."""

from pathlib import Path
from typing import Optional

import typer
import yaml

from everbrain.models.config import EverBrainConfig, RulesConfig
from everbrain.storage.sqlite import DatabaseManager
from everbrain.utils.console import (
    console,
    print_error,
    print_info,
    print_step,
    print_success,
    print_warning,
)
from everbrain.utils.version import get_project_python_version
from everbrain.core.venv import create_internal_venv, install_optimized_dependencies


def init_command(
    project_name: Optional[str] = typer.Option(
        None,
        "--name",
        "-n",
        help="Project name (defaults to current directory name)",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force reinitialize if .everbrain already exists",
    ),
) -> None:
    """Initialize EverBrain in the current project directory.
    
    Creates:
    - .everbrain/ directory structure
    - memory.db SQLite database
    - config.yaml configuration file
    - rules.yaml project rules file
    - AI Automation Protocols (.cursorrules, CLAUDE.md, etc.)
    
    Exits with code 1 if initialization fails.
    """
    try:
        # Step 1: Determine project root and name
        project_root = Path.cwd()
        config_project_name = project_name or project_root.name

        print_step(f"Initializing EverBrain in: {project_root}")
        print_info(f"Project name: {config_project_name}")

        # Step 2: Check if already initialized
        everbrain_dir = project_root / ".everbrain"
        if everbrain_dir.exists() and not force:
            print_warning(
                f".everbrain already exists. Use --force to reinitialize."
            )
            raise typer.Exit(code=1)

        if everbrain_dir.exists() and force:
            print_step("Removing existing .everbrain directory (--force enabled)")
            import shutil

            shutil.rmtree(everbrain_dir)

        # Step 3: Create directory structure
        print_step("Creating .everbrain directory structure...")
        subdirs = [
            everbrain_dir,
            everbrain_dir / "handoffs",
            everbrain_dir / "summaries",
            everbrain_dir / "snapshots",
            everbrain_dir / "sessions",
            everbrain_dir / "graph",
            everbrain_dir / "logs",
        ]
        for subdir in subdirs:
            subdir.mkdir(parents=True, exist_ok=True)

        print_success("Directory structure created")

        # Step 4: Initialize SQLite database
        print_step("Initializing SQLite database...")
        db_path = everbrain_dir / "memory.db"
        db_manager = DatabaseManager(db_path)
        db_manager.initialize_schema()
        db_manager.close()
        print_success("Database initialized")

        # Step 5: Create config.yaml
        print_step("Creating config.yaml...")
        default_config = EverBrainConfig(
            project_name=config_project_name,
            project_root=str(project_root),
            memory_db_path=".everbrain/memory.db",
            log_level="INFO",
            debug_mode=False,
        )
        config_path = everbrain_dir / "config.yaml"
        config_dict = default_config.model_dump()
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
        print_success(f"Config written to {config_path.relative_to(project_root)}")

        # Step 6: Detect Python version and setup internal venv
        print_step("Detecting project environment...")
        python_version = get_project_python_version(project_root)
        print_info(f"Detected Python version: {python_version}")
        
        venv_dir = create_internal_venv(project_root)
        install_optimized_dependencies(venv_dir, python_version)

        # Step 7: Create rules.yaml
        print_step("Creating rules.yaml...")
        default_rules = RulesConfig(
            architecture_notes="Add your architecture documentation here.",
            style_guide={
                "line_length": 100,
                "python_version": python_version,
                "type_checking": "strict",
                "optimization_level": "isolated",
            },
            forbidden_patterns=[],
            metadata={
                "internal_venv": ".everbrain/internal_venv",
                "optimizations": [
                    "Isolated dependencies via internal venv",
                    f"Optimized for Python {python_version}"
                ]
            },
        )
        rules_path = everbrain_dir / "rules.yaml"
        rules_dict = default_rules.model_dump()
        with open(rules_path, "w", encoding="utf-8") as f:
            yaml.dump(rules_dict, f, default_flow_style=False, sort_keys=False)
        print_success(f"Rules written to {rules_path.relative_to(project_root)}")

        # Step 7: Create AI Automation Protocols
        print_step("Generating AI Automation Protocols...")
        
        # 7a. The Master Protocol
        protocol_content = """# EverBrain AI Automation Protocol (V1.5)
You are operating in an EverBrain-managed project. Use the `eb` CLI for all state management.

## 🔄 Workflow Loop
- ON STARTUP: Run `eb summary` to sync with the last session's context.
- BEFORE WORK: Run `eb graph` to visualize dependencies and identify the current blocker.
- WHEN PLANNING: Use `eb task add "<desc>"` (use `--parent <id>` for sub-tasks).
- WHEN SESSIONS END: Run `eb stop` to generate the handoff report.

## 🛡️ Safety & Persistence
- BEFORE MAJOR REFACTORS: Run `eb snapshot "<description>"` to create a recovery point.
- ARCHITECTURE CHANGES: Update `.everbrain/rules.yaml` and run `eb graph --export` to document the new structure.
- SYSTEM STATUS: `eb summary` now persists a report in `.everbrain/summaries/`.

## 🏗️ Architecture Logic
- Dependency Rule: A parent task cannot be marked 'completed' if it has open children.
- Persistence Rule: Never manually edit markdown files in .everbrain; always use the CLI.
"""
        protocol_path = everbrain_dir / "protocol.md"
        with open(protocol_path, "w", encoding="utf-8") as f:
            f.write(protocol_content)

        # 7b. The Router Files
        router_content = "This project uses EverBrain for state management. Before taking any action, read the instructions in `.everbrain/protocol.md` and execute the necessary terminal commands.\n"
        
        # Create root-level router files
        for filename in [".cursorrules", "CLAUDE.md", ".antigravityrules"]:
            with open(project_root / filename, "w", encoding="utf-8") as f:
                f.write(router_content)
                
        # Create GitHub Copilot router file
        github_dir = project_root / ".github"
        github_dir.mkdir(parents=True, exist_ok=True)
        with open(github_dir / "copilot-instructions.md", "w", encoding="utf-8") as f:
            f.write(router_content)

        print_success("AI Automation Protocols generated")

        # Step 8: Success message
        console.print()
        console.print(
            f"✅ EverBrain initialized successfully!",
            style="bold green",
        )
        console.print(
            f"\nNext steps:",
            style="bold cyan",
        )
        console.print(f"  • Review .everbrain/config.yaml")
        console.print(f"  • Add project rules to .everbrain/rules.yaml")
        console.print(f"  • AI Automation Protocols generated for Copilot, Cursor, and Antigravity")
        console.print(f"  • Run: eb start")

    except Exception as e:
        # Graceful error handling: no raw tracebacks
        error_msg = str(e)
        print_error(f"Initialization failed: {error_msg}")
        raise typer.Exit(code=1) from e